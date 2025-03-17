from __future__ import division

import math

from flask import Blueprint, request, Flask, render_template, redirect, url_for

from CTFd.models import db, Solves, Users, Teams
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.utils.decorators import authed_only, during_ctf_time_only, ratelimit, admins_only
from CTFd.utils.modes import get_model

from .models import HavelDockerChallengeModel, HavelDockerSettingsModel
from .compose_manager import ComposeManager


class HavelDockerChallenge(BaseChallenge):
    id = "havel-docker"  # Unique identifier used to register challenges
    name = "havel-docker"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/havel-docker/assets/create.html",
        "update": "/plugins/havel-docker/assets/update.html",
        "view": "/plugins/havel-docker/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/havel-docker/assets/create.js",
        "update": "/plugins/havel-docker/assets/update.js",
        "view": "/plugins/havel-docker/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/havel-docker/assets/"

    challenge_model = HavelDockerChallengeModel


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
            "config": challenge.config,
            "file_path": challenge.file_path,
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

        if not Model is Users and not Model is Teams:
            raise ValueError("HavelDockerChallenge can only be used with Users or Teams")

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
        print(f"Value: {value}")

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

        return HavelDockerChallenge.calculate_value(challenge)

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        HavelDockerChallenge.calculate_value(challenge)


def settings_to_dict(settings):
    return {
        setting.key: setting.value for setting in settings
    }


def load(app: Flask):
    app.db.create_all()
    CHALLENGE_CLASSES["havel-docker"] = HavelDockerChallenge # type: ignore
    register_plugin_assets_directory(
        app, base_path="/plugins/havel-docker/assets/"
    )

    compose_settings: HavelDockerSettingsModel = HavelDockerSettingsModel.query.all()
    if len(compose_settings) == 0:
        compose_settings = HavelDockerSettingsModel()
        db.session.add(compose_settings)
        db.session.commit()
    compose_manager = ComposeManager(compose_settings[0])

    havel_docker_bp = Blueprint(
        'havel-docker',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static',
        url_prefix='/havel-docker',
    )


    @havel_docker_bp.route('/api/start', methods=['POST'])
    @authed_only
    @during_ctf_time_only
    @ratelimit(method="POST", limit=6, interval=60)
    def start_compose():
        if request.json is None:
            return {"error": "Invalid request"}, 400
        if request.json.get("challenge_id") is None:
            return {"error": "No challenge_id provided"}, 400

        challenge_id = request.json.get("challenge_id")
        challenge = HavelDockerChallengeModel.query.filter_by(id=challenge_id).first()
        if challenge is None:
            return {"error": "Invalid challenge_id"}, 400

        try:
            compose_manager.run(f"compose-{challenge.id}.yml", challenge.config)
        except Exception as e:
            return {"error": str(e)}, 500

        return {"success": "Compose started successfully"}, 200


    @havel_docker_bp.route('/api/stop', methods=['POST'])
    @authed_only
    @during_ctf_time_only
    @ratelimit(method="POST", limit=6, interval=60)
    def stop_compose():
        if request.json is None:
            return {"error": "Invalid request"}, 400
        if request.json.get("challenge_id") is None:
            return {"error": "No challenge_id provided"}, 400

        challenge_id = request.json.get("challenge_id")
        challenge = HavelDockerChallengeModel.query.filter_by(id=challenge_id).first()
        if challenge is None:
            return {"error": "Invalid challenge_id"}, 400

        try:
            compose_manager.stop(f"compose-{challenge.id}.yml")
        except Exception as e:
            return {"error": str(e)}, 500

        return {"success": "Compose stopped successfully"}, 200


    @havel_docker_bp.route('/api/reset', methods=['POST'])
    @authed_only
    @during_ctf_time_only
    @ratelimit(method="POST", limit=6, interval=60)
    def reset_compose():
        if request.json is None:
            return {"error": "Invalid request"}, 400
        if request.json.get("challenge_id") is None:
            return {"error": "No challenge_id provided"}, 400

        challenge_id = request.json.get("challenge_id")
        challenge = HavelDockerChallengeModel.query.filter_by(id=challenge_id).first()
        if challenge is None:
            return {"error": "Invalid challenge_id"}, 400

        try:
            compose_manager.reset(f"compose-{challenge.id}.yml", challenge.config)
        except Exception as e:
            return {"error": str(e)}, 500

        return {"success": "Compose reset successfully"}, 200


    @havel_docker_bp.route('/api/status', methods=['POST'])
    @authed_only
    @during_ctf_time_only
    def is_compose_running():
        if request.json is None:
            return {"error": "Invalid request"}, 400
        if request.json.get("challenge_id") is None:
            return {"error": "No challenge_id provided"}, 400

        challenge_id = request.json.get("challenge_id")
        challenge = HavelDockerChallengeModel.query.filter_by(id=challenge_id).first()
        if challenge is None:
            return {"error": "Invalid challenge_id"}, 400

        is_running = compose_manager.is_running(f"compose-{challenge.id}.yml")

        return {"status": "running" if is_running else "stopped"}, 200


    @havel_docker_bp.route('/api/settings', methods=['GET'])
    @authed_only
    @during_ctf_time_only
    def get_settings():
        settings = compose_manager.get_settings()
        return settings, 200


    @havel_docker_bp.route('/api/settings', methods=['POST'])
    @admins_only
    def set_settings():
        if request.form.get("hostname") is None:
            return {"error": "Invalid request"}, 400

        settings = {
            "hostname": request.form.get("hostname")
        }
        compose_manager.set_settings(settings)

        return redirect(url_for(".route_compose_dashboard"))


    @havel_docker_bp.route('/settings', methods=['GET'])
    @admins_only
    def route_compose_settings():
        settings = compose_manager.get_settings()
        return render_template('compose_settings.html', settings=settings)


    @havel_docker_bp.route('/dashboard', methods=['GET'])
    @admins_only
    def route_compose_dashboard():
        challenges = HavelDockerChallengeModel.query.all()

        for challenge in challenges:
            challenge.is_running = compose_manager.is_running(f"compose-{challenge.id}.yml")

        return render_template('compose_dashboard.html', challenges=challenges)


    app.register_blueprint(havel_docker_bp)
