from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class VehicleRecord(db.Model):
    __tablename__ = "vehicle_records"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(64), nullable=False)
    vtype = db.Column(db.String(32), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    slot = db.Column(db.Integer, nullable=False)
    fee = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "vtype": self.vtype,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "slot": self.slot,
            "fee": self.fee
        }

def init_db():
    db.create_all()
