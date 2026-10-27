from .models import Blocked


class PositionManager:
    def __init__(self, execution):
        self.e = execution

    def run(self):
        results = []
        for op in self.e.j.operations():
            if op["status"] != "CONFIRMED" or op["payload"]["rule"] != "OPEN":
                continue
            op = self.e.j.effective_operation(op)
            env = op["payload"]["envelope"]
            snap = self.e.b.snapshot()
            for o in snap["orders"]:
                if o["ticket"] == op["result"]["order"]:
                    results.append(self.attempt(env, "CANCEL_PENDING", o["ticket"]))
            # Active pending orders may not yet exist in history_orders_get(ticket).
            # Reconciliation handles partial activation; refresh on the next cycle.
            if any(o['ticket'] == op['result']['order'] for o in snap['orders']):
                continue
            hist = self.e.b.order_history(op["result"]["order"])
            ids = {o.get("position_id") for o in hist if o.get("position_id")}
            for p in snap["positions"]:
                if p["identifier"] not in ids:
                    continue
                for rule in ("STOP_CLOSE", "INVALIDATION", "TP2", "TP1", "BREAK_EVEN", "TRAILING"):
                    result = self.attempt(env, rule, p["ticket"])
                    results.append(result)
                    if result["status"] in {"CONFIRMED", "UNCERTAIN", "DRY_RUN"}:
                        break  # Refresh the position on the next cycle before another change.
        return results

    def attempt(self, env, rule, ticket):
        try:
            return {"signal_id": env["signal"]["id"], "rule": rule, **self.e.execute(env, rule, ticket)}
        except Blocked as exc:
            result = {"signal_id": env["signal"]["id"], "rule": rule, "ticket": ticket,
                      "status": "HELD", "reason": str(exc)}
            self.e.j.event("management_decision", result)
            return result
