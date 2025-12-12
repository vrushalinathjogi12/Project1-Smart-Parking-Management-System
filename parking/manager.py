from parking.storage import Storage
from datetime import datetime, date
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ParkingManager:

    def __init__(self, app, settings: dict):
        self.app = app
        self.settings = settings
        self.total_slots = int(settings.get("total_slots", 24))
        self.vip_slots = set(settings.get("vip_slots", []))
        self.storage = Storage(total_slots=self.total_slots)

    # ---------------------------
    # STATUS
    # ---------------------------
    def current_status(self):
        occupied = self.storage.get_all_occupied()
        free_slots = [i for i in range(1, self.total_slots + 1)
                      if i not in [v["slot"] for v in occupied]]
        return {
            "total_slots": self.total_slots,
            "occupied_count": len(occupied),
            "free_count": len(free_slots),
            "free_slots": free_slots,
            "occupied": occupied,
            "vip_slots": sorted(list(self.vip_slots))
        }

    def find_next_free_slot(self, prefer_vip=False):
        if prefer_vip:
            for s in sorted(self.vip_slots):
                if self.storage.slots.get(s) is None:
                    return s
        for i in range(1, self.total_slots + 1):
            if self.storage.slots.get(i) is None:
                return i
        return None

    def park_vehicle(self, number, vtype="car", is_vip=False):
        existing = self.storage.find_vehicle_slot(number)
        if existing:
            raise RuntimeError(f"Vehicle {number} already parked at slot {existing}.")
        slot = self.find_next_free_slot(prefer_vip=is_vip)
        if not slot:
            raise RuntimeError("Parking full")
        vehicle = {"number": number, "vtype": vtype,
                   "entry_time": datetime.now().isoformat(),
                   "slot": slot, "is_vip": is_vip}
        self.storage.save_parked(slot, vehicle)
        return vehicle

    def exit_vehicle(self, number, billing_engine):
        slot = self.storage.find_vehicle_slot(number)
        if not slot:
            raise RuntimeError("Vehicle not found")
        vehicle = self.storage.slots[slot]
        entry_time = datetime.fromisoformat(vehicle["entry_time"])
        exit_time = datetime.now()
        charge = billing_engine.calculate_fee(entry_time, exit_time, vehicle["vtype"])
        self.storage.remove_vehicle(slot)
        self.storage.persist_exit(vehicle, charge["fee"], exit_time)
        return {
            "vehicle_number": vehicle["number"],
            "vtype": vehicle["vtype"],
            "entry": vehicle["entry_time"],
            "exit": exit_time.isoformat(),
            "slot": slot,
            "fee": charge["fee"],
            "charge_meta": charge
        }

    # ---------------------------
    # DAILY SUMMARY
    # ---------------------------
    def daily_revenue_summary(self, qdate: date):
        records = self.storage.get_daily_records(qdate)
        total = sum(r["fee"] for r in records)
        for v in self.storage.get_all_occupied():
            records.append({
                "vehicle_number": v["number"],
                "vtype": v["vtype"],
                "entry": v["entry_time"],
                "exit": None,
                "slot": v["slot"],
                "fee": 0
            })
        return {
            "date": qdate.isoformat(),
            "total_vehicles": len(records),
            "total_revenue": total,
            "records": records
        }

    # ---------------------------
    # PDF REPORT
    # ---------------------------
    def generate_pdf_daily_report(self, qdate: date):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab not installed")

        summary = self.daily_revenue_summary(qdate)
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        fname = reports_dir / f"daily_report_{summary['date']}.pdf"

        c = canvas.Canvas(str(fname), pagesize=A4)
        width, height = A4
        type_colors = {"car": colors.blue, "bike": colors.green,
                       "ev": colors.purple, "heavy": colors.red}

        # HEADER
        c.setFont("Helvetica-Bold", 18)
        c.drawString(20*mm, height - 20*mm, "Smart Parking - Daily Report")
        c.setFont("Helvetica", 11)
        c.drawString(20*mm, height - 27*mm, f"Date: {summary['date']}")
        c.drawString(20*mm, height - 34*mm, f"Total Vehicles: {summary['total_vehicles']}")
        c.drawString(20*mm, height - 41*mm, f"Total Revenue: ₹ {summary['total_revenue']:.2f}")

        y = height - 55*mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(15*mm, y, "Slot")
        c.drawString(35*mm, y, "Vehicle")
        c.drawString(75*mm, y, "Type")
        c.drawString(100*mm, y, "Entry")
        c.drawString(145*mm, y, "Exit")
        c.drawString(180*mm, y, "Fee")
        y -= 7*mm
        c.setFont("Helvetica", 10)

        for rec in summary["records"]:
            if y < 20*mm:
                c.showPage()
                y = height - 20*mm
                c.setFont("Helvetica-Bold", 11)
                c.drawString(15*mm, y, "Slot")
                c.drawString(35*mm, y, "Vehicle")
                c.drawString(75*mm, y, "Type")
                c.drawString(100*mm, y, "Entry")
                c.drawString(145*mm, y, "Exit")
                c.drawString(180*mm, y, "Fee")
                y -= 7*mm
                c.setFont("Helvetica", 10)

            if rec["slot"] in self.vip_slots:
                c.setFillColor(colors.gold)
                c.rect(12*mm, y - 2*mm, 185*mm, 8*mm, fill=1, stroke=0)
                c.setFillColor(colors.black)

            c.drawString(15*mm, y, str(rec["slot"]))
            c.drawString(35*mm, y, rec["vehicle_number"])
            vtype = rec["vtype"]
            c.setFillColor(type_colors.get(vtype, colors.black))
            c.drawString(75*mm, y, vtype.upper())
            c.setFillColor(colors.black)

            c.drawString(100*mm, y, (rec["entry"] or "")[:16])
            c.drawString(145*mm, y, (rec["exit"] or "Pending")[:16])
            c.drawString(180*mm, y, f"₹ {rec['fee']:.2f}")

            y -= 7*mm

        c.save()
        return str(fname)
