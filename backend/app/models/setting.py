from app.extensions import db


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
