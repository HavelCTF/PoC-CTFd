from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from CTFd.models import db
from CTFd.models import Challenges


class HavelChallengeModel(Challenges):
    __mapper_args__ = {"polymorphic_identity": "havel"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    camion = db.Column(db.Text, default="")

    # Dynamic challenge properties
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)

    def __init__(self, *args, **kwargs):
        super(HavelChallengeModel, self).__init__(**kwargs)
        self.value = kwargs["initial"]
