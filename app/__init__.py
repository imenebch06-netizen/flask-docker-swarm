from flask import Flask
from flasgger import Swagger
from app.controllers.system_controller import system_bp

def create_app():
    app = Flask(__name__)
    Swagger(app)
    app.register_blueprint(system_bp)
    return app
