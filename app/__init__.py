from flask import Flask
from flask import redirect, url_for
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev'),
        YOUTUBE_CLIENT_SECRETS=os.environ.get('YOUTUBE_CLIENT_SECRETS', 'client_secret_289773002327-f3t5si3na5v4mnfkrh9qpne2pvl2qr3j.apps.googleusercontent.com.json'),
        YOUTUBE_API_SERVICE_NAME='youtube',
        YOUTUBE_API_VERSION='v3',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    # Register blueprints/routes
    from . import routes
    app.register_blueprint(routes.bp)

    from .bans_page import bp_bans
    app.register_blueprint(bp_bans)

    @app.route('/')
    def index():
        return redirect(url_for('routes.home'))

    return app
