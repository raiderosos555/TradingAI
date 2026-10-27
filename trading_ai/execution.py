from __future__ import annotations

from .models import Blocked, canonical, digest


def expiration_matches(actual, requested):
    # This broker truncates specified expiration to a whole minute. Earlier
    # expiry narrows the approved lifetime; never accept an extension or zero.
    return requested > 0 and actual > 0 and actual in {requested, requested // 60 * 60}


class ExecutionEngine:
    def __init__(self, risk):
        self.risk, self.b, self.j = risk, risk.b, risk.j

    def execute(self, env, rule="OPEN", ticket=None, new_sl=None, old_env=None, close_volume=None, operation_id=None):
        self.j.register(env)
        if rule == "OPEN" and self.j.root_id(env) != env["signal"]["id"]:
            raise Blocked("Signal already used as a pending amendment")
        def prepare():
            if rule == "OPEN":
                return self.risk.prepare_open(env)
            if rule == "TIGHTEN_PENDING":
                return self.risk.prepare_pending_tighten(env, ticket, new_sl)
            if rule == "AMEND_PENDING":
                return self.risk.prepare_open(env, replacement=(old_env, ticket))
            return self.risk.prepare_managed(env, rule, ticket, close_volume)
        request, metadata = prepare()
        key = "open:" + env["signal"]["id"] if rule == "OPEN" else f'{rule}:{env["signal"]["id"]}:{ticket}'
        if rule in {"TRAILING", "TIGHTEN_PENDING"}:
            key += ":" + digest(request)[:16]
        if operation_id:
            from .models import identifier
            identifier(operation_id)
            key += ":" + operation_id
        if self.j.operation(key):
            raise Blocked("Operation already recorded; never resend automatically")
        payload = {"envelope": env, "rule": rule, "request": request, "metadata": metadata}
        check = self.b.check(request)
        if check.get("retcode") != 0:
            raise Blocked(f'Broker order_check rejected: {check.get("retcode")} {check.get("comment", "")}')
        if self.risk.c["mode"] == "DRY_RUN":
            self.j.event("dry_run", payload)
            return {"status": "DRY_RUN", **payload}
        # Re-read broker state and repeat the independent gate after order_check.
        latest, latest_metadata = prepare()
        if canonical(latest) != canonical(request):
            raise Blocked("Broker state changed during preflight; re-evaluate next cycle")
        payload["metadata"] = latest_metadata
        if self.risk.c["mode"] == "DRY_RUN":
            self.j.event("dry_run", payload)
            return {"status": "DRY_RUN", **payload}
        self.j.intent(key, payload)  # Durable BEFORE sending, including after process crash.
        try:
            result = self.b.send(request)
            self.j.finish(key, "UNCERTAIN", result)
            if result.get("retcode") not in {10008, 10009}:
                # Includes DONE_PARTIAL, timeout, rejection and any unrecognized broker result.
                # No retry: conservative quarantine, requiring evidence/operator reconciliation.
                self.j.event("uncertain", {"id": key, "result": result})
                return {"status": "UNCERTAIN", "result": result}
            op = self.j.operation(key)
            if not self.verify(op):
                self.j.event("uncertain", {"id": key, "reason": "Broker result not confirmed by actual state"})
                return {"status": "UNCERTAIN", "result": result}
            self.j.finish(key, "CONFIRMED", result)
            self.apply_effects(self.j.operation(key))
            self.j.event("confirmed", {"id": key, "result": result, "reason": env["signal"]["reason"] if rule == "OPEN" else rule})
            return {"status": "CONFIRMED", "result": result}
        except Exception as exc:
            self.j.event("uncertain", {"id": key, "error": str(exc)})
            raise Blocked("Send/verification interrupted: durable intent blocks all further orders") from exc

    def verify(self, op):
        payload, result = op["payload"], op["result"] or {}
        req, rule = payload["request"], payload["rule"]
        snap = self.b.snapshot()
        a = snap["account"]
        if a["login"] != self.risk.c["account_login"] or a["server"] != self.risk.c["account_server"]:
            return False
        if rule == "OPEN":
            order = result.get("order")
            if not order:
                return False
            pending = [o for o in snap["orders"] if o["ticket"] == order]
            if pending:
                p = pending[0]
                return (req["action"] == 5 and p["magic"] == req["magic"] and p["comment"] == req["comment"]
                        and p["symbol"] == req["symbol"] and p["type"] == req["type"]
                        and abs(p["volume_current"]-req["volume"]) < 1e-8
                        and abs(p["price_open"]-req["price"]) < 1e-8
                        and p["sl"] == req["sl"] and p["tp"] == req["tp"]
                        and expiration_matches(p["time_expiration"], req["expiration"]))
            # Resolve the stable POSITION_IDENTIFIER using the broker's order history.
            history = self.b.order_history(order)
            if req["action"] == 5 and len(history) == 1 and history[0].get("state") in {2, 6} and not history[0].get("position_id"):
                h = history[0]
                return (h.get("magic") == req["magic"] and h.get("symbol") == req["symbol"]
                        and h.get("comment") == req["comment"] and h.get("type") == req["type"]
                        and abs(h.get("volume_initial", -1)-req["volume"]) < 1e-8)
            if len(history) != 1 or not history[0].get("position_id"):
                return False
            pid = history[0]["position_id"]
            deals = self.b.position_deals(pid)
            opens = [d for d in deals if d["order"] == order and d["entry"] == 0 and d["type"] in {0, 1}]
            if not opens or abs(sum(d["volume"] for d in opens) - req["volume"]) > 1e-8:
                return False
            if any(d["magic"] != req["magic"] or d["symbol"] != req["symbol"] or d["type"] != req["type"] % 2 for d in opens):
                return False
            if any(d["type"] in {0, 1} and (d["magic"] != req["magic"] or d["entry"] not in {0, 1}
                       or d["entry"] == 0 and d["order"] != order) for d in deals):
                return False
            positions = [p for p in snap["positions"] if p["identifier"] == pid]
            if positions and any(p["sl"] != req["sl"] or p["tp"] != req["tp"] or p["magic"] != req["magic"] for p in positions):
                return False
            allowance = payload["metadata"].get("fill_deviation_price")
            if allowance is None:  # Legacy entry intents still retain requested deviation.
                allowance = req["deviation"] * self.b.market(req["symbol"])["info"]["point"]
            reference = payload["metadata"]["entry_reference"]
            # Any fill beyond configured deviation quarantines the engine, including gaps on pending stops.
            if any((d["price"] - reference) * (1 if req["type"] % 2 == 0 else -1) > allowance + 1e-8 for d in opens):
                return False
            return True
        before = payload["metadata"]["target_before"]
        if rule in {"TIGHTEN_PENDING", "AMEND_PENDING"}:
            orders = [o for o in snap["orders"] if o["ticket"] == req["order"]]
            return (len(orders) == 1 and orders[0]["sl"] == req["sl"] and orders[0]["tp"] == req["tp"]
                    and orders[0]["price_open"] == req["price"] and orders[0]["magic"] == req["magic"]
                    and orders[0]["volume_current"] == before["volume_current"]
                    and expiration_matches(orders[0]["time_expiration"], req["expiration"]))
        if rule in {"CANCEL_PENDING", "OPERATOR_CANCEL"}:
            if any(p["ticket"] == req["order"] for p in snap["orders"]):
                return False
            hist = self.b.order_history(req["order"])
            return len(hist) == 1 and hist[0]["state"] in {2, 6}  # canceled or expired, not filled
        positions = [p for p in snap["positions"] if p["identifier"] == before["identifier"]]
        if req["action"] == 6:
            return len(positions) == 1 and positions[0]["sl"] == req["sl"] and positions[0]["tp"] == req["tp"]
        deals = [d for d in self.b.position_deals(before["identifier"])
                 if d["order"] == result.get("order") and d["entry"] == 1 and d["magic"] == req["magic"]]
        remaining = sum(p["volume"] for p in positions)
        reference = payload["metadata"].get("entry_reference")
        allowance = payload["metadata"].get("fill_deviation_price")
        if reference is None or allowance is None:
            return False  # Missing historical quote is not proof of an acceptable fill.
        if any(d.get("symbol") != req["symbol"] or d.get("type") != req["type"]
               or (d["price"]-reference) * (1 if req["type"] == 0 else -1) > allowance + 1e-8
               for d in deals):
            return False
        return (bool(deals) and abs(sum(d["volume"] for d in deals)-req["volume"]) < 1e-8
                and abs(remaining - (before["volume"]-req["volume"])) < 1e-8)

    def apply_effects(self, op):
        if op["payload"]["rule"] in {"AMEND_PENDING", "TIGHTEN_PENDING"}:
            old = op["payload"]["metadata"].get("original_envelope", op["payload"]["envelope"])
            root = self.j.root_id(old)
            new_id = op["payload"]["envelope"]["signal"]["id"]
            self.j.set_setting("root_signal:"+new_id, root)
            self.j.set_setting("effective:"+root, op["id"])

    def audit_pending_activation(self, op):
        """Verify the first broker-side activation before any local position management."""
        if op["payload"]["rule"] != "OPEN" or op["payload"]["request"]["action"] != 5:
            return None
        key = "activation_verified:"+op["id"]
        if self.j.setting(key):
            return None
        effective = self.j.effective_operation(op)
        order = op["result"]["order"]
        if any(o["ticket"] == order for o in self.b.snapshot()["orders"]):
            if self.verify(effective):
                return None
            self.j.finish(op["id"], "UNCERTAIN", op["result"])
            reason = "Pending order differs from approved state, including possible residual partial fill"
            self.j.event("pending_activation_uncertain", {"id":op["id"], "reason":reason})
            return {"id":op["id"], "status":"UNCERTAIN", "reason":reason}
        if self.verify(effective):
            self.j.set_setting(key, True)
            self.j.event("pending_activation_verified", {"id":op["id"], "order":order})
            return {"id":op["id"], "status":"CONFIRMED", "reason":"Pending execution or cancellation verified against broker history"}
        self.j.finish(op["id"], "UNCERTAIN", op["result"])
        reason = "Pending activation lacks matching volume, ownership, protective levels or acceptable fill price"
        self.j.event("pending_activation_uncertain", {"id":op["id"], "reason":reason})
        return {"id":op["id"], "status":"UNCERTAIN", "reason":reason}

    def accept_partial(self, key, note):
        """Explicit operator reconciliation, no order send and no automatic topping up."""
        import copy
        if not isinstance(note, str) or not note.strip():
            raise Blocked("Operator reconciliation note required")
        op = self.j.operation(key)
        if not op or op["status"] != "UNCERTAIN" or op["payload"]["rule"] != "OPEN" or (op["result"] or {}).get("retcode") != 10010:
            raise Blocked("Only an explicitly reported partial OPEN can be adopted")
        snap = self.b.snapshot()
        order = op["result"].get("order")
        if any(o["ticket"] == order for o in snap["orders"]):
            raise Blocked("Residual pending volume remains at broker; do not adopt yet")
        history = self.b.order_history(order)
        if len(history) != 1 or not history[0].get("position_id"):
            raise Blocked("Partial execution history unavailable")
        deals = self.b.position_deals(history[0]["position_id"])
        volume = sum(d["volume"] for d in deals if d["order"] == order and d["entry"] == 0 and d["type"] in {0,1})
        if not 0 < volume <= op["payload"]["request"]["volume"]:
            raise Blocked("Partial volume does not fit original intent")
        trial = copy.deepcopy(op)
        trial["payload"]["request"]["volume"] = volume
        if not self.verify(trial):
            raise Blocked("Partial execution lacks matching ownership, protection or fill evidence")
        result = {**op["result"], "accepted_volume": volume, "operator_note": note}
        self.j.finish(key,"CONFIRMED",result)
        self.j.event("operator_accept_partial", {"id":key, "volume":volume, "note":note})
        return {"id":key,"status":"CONFIRMED","accepted_volume":volume,"orders_sent":0}

    def reconcile(self):
        outcomes = []
        # Replay all amendments before checking any subsequently activated order.
        for op in self.j.operations():
            if op["status"] == "CONFIRMED":
                self.apply_effects(op)
        for op in self.j.operations():
            if op["status"] == "CONFIRMED":
                audit = self.audit_pending_activation(op)
                if audit:
                    outcomes.append(audit)
                continue
            if op["status"] not in {"INTENT", "UNCERTAIN"}:
                continue
            if not (op["result"] or {}).get("order") and op["payload"]["rule"] == "OPEN":
                from datetime import timedelta
                from .models import timestamp, utcnow
                request = op["payload"]["request"]
                snap = self.b.snapshot()
                if [snap["account"]["login"], snap["account"]["server"]] != [self.risk.c["account_login"], self.risk.c["account_server"]]:
                    raise Blocked("Cannot reconcile across accounts")
                if callable(getattr(self.b, "history", None)):
                    history = self.b.history(timestamp(op["at"])-timedelta(minutes=1), utcnow())
                    candidates = {o["ticket"] for o in snap["orders"]+history["orders"]
                                  if o.get("magic") == request["magic"] and o.get("comment") == request["comment"]
                                  and o.get("symbol") == request["symbol"] and o.get("type") == request["type"]}
                    if len(candidates) == 1:
                        recovered = {"order": candidates.pop(), "recovered_from_broker_history": True,
                                     "note": "Original send response unavailable; no operation was resent"}
                        trial = {**op, "result": recovered}
                        if self.verify(trial):
                            self.j.finish(op["id"], "CONFIRMED", recovered)
                            self.apply_effects(self.j.operation(op["id"]))
                            self.j.event("recovered_intent", {"id": op["id"], "evidence": recovered})
                            outcomes.append({"id": op["id"], "status": "CONFIRMED"})
                            continue
            # Partial fills stay quarantined even if an eventual remainder appears.
            known = (op["result"] or {}).get("retcode") in {10008, 10009}
            if known and self.verify(self.j.effective_operation(op) if op["payload"]["rule"] == "OPEN" else op):
                self.j.finish(op["id"], "CONFIRMED", op["result"])
                self.apply_effects(self.j.operation(op["id"]))
                self.j.event("reconciled", {"id": op["id"]})
                outcomes.append({"id": op["id"], "status": "CONFIRMED"})
            else:
                outcomes.append({"id": op["id"], "status": "UNCERTAIN", "reason": "Manual broker reconciliation required; never auto-resend"})
        return outcomes
