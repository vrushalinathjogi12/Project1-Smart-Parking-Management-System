from datetime import datetime
import math

class BillingEngine:
    def __init__(self, settings: dict):
        self.first_hours = int(settings.get("first_hours", 2))
        self.first_fee = float(settings.get("first_hours_fee", 20.0))
        self.per_hour_fee = float(settings.get("per_hour_fee", 10.0))
        self.mult = settings.get("vehicle_type_multiplier", {"car":1.0})

    def calculate_fee(self, entry_dt: datetime, exit_dt: datetime, vtype: str) -> dict:
        if exit_dt < entry_dt:
            raise ValueError("Exit before entry")
        duration = exit_dt - entry_dt
        total_seconds = duration.total_seconds()
        exact_hours = total_seconds / 3600.0

        if exact_hours <= self.first_hours:
            fee = self.first_fee
            charged_hours = self.first_hours
            extra_hours = 0
        else:
            extra = exact_hours - self.first_hours
            extra_hours = math.ceil(extra)
            fee = self.first_fee + extra_hours * self.per_hour_fee
            charged_hours = self.first_hours + extra_hours

        multiplier = float(self.mult.get(vtype, 1.0))
        fee = round(fee * multiplier + 1e-9, 2)
        return {
            "duration_seconds": int(total_seconds),
            "duration_hours": exact_hours,
            "charged_hours": charged_hours,
            "extra_hours": extra_hours,
            "fee": fee,
            "multiplier": multiplier
        }
