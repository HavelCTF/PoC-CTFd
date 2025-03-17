from CTFd.exceptions.challenges import (
    ChallengeCreateException,
)
from CTFd.models import db
from CTFd.models import Challenges

from .compose_manager import ComposeManager


class HavelDockerChallengeModel(Challenges):
    __mapper_args__ = {"polymorphic_identity": "havel-docker"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    config = db.Column(db.Text, default="")
    file_path = db.Column(db.Text, default="")

    # Dynamic challenge properties
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)

    def __init__(self, *args, **kwargs):
        super(HavelDockerChallengeModel, self).__init__(**kwargs)
        self.value = kwargs["initial"]

        is_valid = False
        try:
            is_valid = ComposeManager.check(f"compose-{self.id}.yml", self.config)
        except Exception as e:
            raise ChallengeCreateException(e)

        if not is_valid:
            raise ChallengeCreateException("Invalid docker compose configuration")


class HavelDockerSettingsModel(db.Model):
    __mapper_args__ = {"polymorphic_identity": "havel-docker-settings"}
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(128), default="[No hostname set]")
