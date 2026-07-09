# ... (bestehender Code von v9.2)

try:
    from .coevolutionary_closure import get_coevolutionary_closure, CoEvolutionaryClosure
except Exception:
    CoEvolutionaryClosure = None
    get_coevolutionary_closure = None


class AscensionCore:
    def __init__(self):
        ...
        # CoevolutionaryClosure Integration
        self.cec: Optional[CoEvolutionaryClosure] = None
        if get_coevolutionary_closure:
            self.cec = get_coevolutionary_closure()

    def get_ascension_status(self) -> Dict[str, Any]:
        status = { ... }
        if self.cec:
            status["cec_status"] = self.cec.get_status()
        return status

    def notify_coevolutionary_change(self, source: str, change_type: str, payload: Dict[str, Any]):
        if self.cec:
            self.cec.notify_change(source, change_type, payload)
