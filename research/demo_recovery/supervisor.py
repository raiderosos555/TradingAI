"""Offline supervision policy. No broker/order API and no production deployment."""
from dataclasses import dataclass

@dataclass
class SupervisorPolicy:
    max_failures:int=3
    failures:int=0
    retry_at:float=0

    def decide(self,now,*,enabled=True,child_alive=False,heartbeat_fresh=True,lock_free=True):
        if not enabled:return 'DISABLED'
        if child_alive:return 'OBSERVE' if heartbeat_fresh else 'ALERT_STALLED_NO_DUPLICATE'
        if not lock_free:return 'EXISTING_OWNER_NO_START'
        if self.failures>=self.max_failures:return 'CIRCUIT_OPEN'
        if now<self.retry_at:return 'BACKOFF'
        return 'START'

    def failed(self,now):
        self.failures+=1
        self.retry_at=now+min(60,2**(self.failures-1))
