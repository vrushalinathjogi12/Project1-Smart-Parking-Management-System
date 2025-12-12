# fixed storage.py
from typing import Dict, Optional
from datetime import datetime, date
from parking.models import db, VehicleRecord


class Storage:
    """
    In-memory slot management + SQL persistence for completed parking records.
    Active parked vehicles stay in memory.
    Completed exits are stored in the DB.
    """

    def __init__(self, total_slots=24):
        self.total_slots = total_slots
        # slot → vehicle or None
        self.slots = {i: None for i in range(1, total_slots + 1)}

    # ------------------------------ ACTIVE PARKING ------------------------------

    def save_parked(self, slot: int, vehicle: dict):
        self.slots[slot] = vehicle

    def remove_vehicle(self, slot: int):
        self.slots[slot] = None

    def find_vehicle_slot(self, number: str):
        for s, v in self.slots.items():
            if v and v.get("number") == number:
                return s
        return None

    def get_all_occupied(self):
        return [v for v in self.slots.values() if v is not None]

    # ------------------------------ EXIT / SAVE TO DB ------------------------------

    def persist_exit(self, vehicle: dict, fee: float, exit_time: datetime):
        """Store completed parking in database."""
        rec = VehicleRecord(
            number=vehicle["number"],
            vtype=vehicle["vtype"],
            entry_time=datetime.fromisoformat(vehicle["entry_time"]),
            exit_time=exit_time,
            slot=vehicle["slot"],
            fee=float(fee)
        )
        db.session.add(rec)
        db.session.commit()

    # ------------------------------ DAILY REPORT FIXED ------------------------------

    def get_daily_records(self, query_date: date):
        """
        Correctly return all records where exit_time.date() == query_date.
        Uses proper SQL date comparison.
        """
        results = VehicleRecord.query.filter(
            db.func.date(VehicleRecord.exit_time) == query_date  # <-- FIXED
        ).all()

        final = []
        for r in results:
            final.append({
                "vehicle_number": r.number,
                "vtype": r.vtype,
                "entry": r.entry_time.isoformat(),
                "exit": r.exit_time.isoformat(),
                "slot": r.slot,
                "fee": float(r.fee)
            })
        return final
