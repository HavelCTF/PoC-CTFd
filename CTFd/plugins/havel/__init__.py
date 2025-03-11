from flask import Blueprint

from CTFd.exceptions.challenges import (
    ChallengeCreateException,
    ChallengeUpdateException,
)
from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.migrations import upgrade


class HavelChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "havel"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    camion = db.Column(db.String(2048), default="")

    def __init__(self, *args, **kwargs):
        super(HavelChallenge, self).__init__(**kwargs)
        try:
            self.value = kwargs["camion"]
        except KeyError:
            raise ChallengeCreateException("Missing camion value for challenge")


class HavelValueChallenge(BaseChallenge):
    id = "havel"  # Unique identifier used to register challenges
    name = "havel"  # Name of a challenge type
    templates = (
        {  # Handlebars templates used for each aspect of challenge editing & viewing
            "create": "/plugins/havel/assets/create.html",
            "update": "/plugins/havel/assets/update.html",
            "view": "/plugins/havel/assets/view.html",
        }
    )
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/havel/assets/create.js",
        "update": "/plugins/havel/assets/update.js",
        "view": "/plugins/havel/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/havel/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "havel",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = HavelChallenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = HavelChallenge.query.filter_by(id=challenge.id).first()
        data = super().read(challenge)
        data.update(
            {
                "camion": challenge.camion,
            }
        )
        return data

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)


def load(app):
    upgrade(plugin_name="havel")
    CHALLENGE_CLASSES["havel"] = HavelValueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/havel/assets/"
    )
    register_plugin_assets_directory(
        app, base_path="/plugins/havel/static/", endpoint="havel.static"
    )
