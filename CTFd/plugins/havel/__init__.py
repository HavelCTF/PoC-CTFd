from __future__ import division

import time
import json
import datetime
import math

from flask import Blueprint, request, Flask, render_template, url_for, redirect, flash

from CTFd.models import db, Solves
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.utils.decorators import authed_only, admins_only, during_ctf_time_only, ratelimit, require_verified_emails
from CTFd.utils.user import get_current_user
from CTFd.utils.modes import get_model

from .models import HavelChallengeModel


class HavelChallenge(BaseChallenge):
    id = "havel"  # Unique identifier used to register challenges
    name = "havel"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/havel/assets/create.html",
        "update": "/plugins/havel/assets/update.html",
        "view": "/plugins/havel/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/havel/assets/create.js",
        "update": "/plugins/havel/assets/update.js",
        "view": "/plugins/havel/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/havel/assets/"

    challenge_model = HavelChallengeModel

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "camion": challenge.camion,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "connection_info": challenge.connection_info,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def calculate_value(cls, challenge):
        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
            .filter(
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
            .count()
        )

        # If the solve count is 0 we shouldn't manipulate the solve count to
        # let the math update back to normal
        if solve_count != 0:
            # We subtract -1 to allow the first solver to get max point value
            solve_count -= 1

        # It is important that this calculation takes into account floats.
        # Hence this file uses from __future__ import division
        value = (
            ((challenge.minimum - challenge.initial) / (challenge.decay ** 2))
            * (solve_count ** 2)
        ) + challenge.initial

        value = math.ceil(value)

        if value < challenge.minimum:
            value = challenge.minimum

        challenge.value = value
        db.session.commit()
        return challenge

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.
        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        return HavelChallenge.calculate_value(challenge)

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        HavelChallenge.calculate_value(challenge)


def load(app: Flask):
    app.db.create_all()
    CHALLENGE_CLASSES["havel"] = HavelChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/havel/assets/"
    )
    register_plugin_assets_directory(
        app, base_path="/plugins/havel/static/", endpoint="havel.static"
    )
