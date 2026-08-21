import os
import time
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text
from flask import Flask, jsonify, g
from flasgger import Swagger
from app.models.user import db
from app.controllers.system_controller import system_bp

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/cvdb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PDF_DIRECTORY'] = os.getenv('PDF_DIRECTORY', '/shared_pdf')

    db.init_app(app)

    with app.app_context():
        last_error = None
        for _ in range(15):
            try:
                db.create_all()
                migrate_user_columns()
                break
            except SQLAlchemyError as error:
                last_error = error
                db.session.remove()
                time.sleep(2)
        else:
            raise last_error

    # Configuration Swagger
    swagger_template = {
        "swagger": "2.0",
        "info": {"title": "API Swarm & Flask Deep-Dive", "version": "2.0.0"}
    }
    Swagger(app, template=swagger_template)

    # --- 1. HOOKS FLASK (Cycles de vie) ---
    @app.before_request
    def start_timer():
        # 'g' est l'objet global Flask propre à chaque requête HTTP
        g.start_time = time.time()

    @app.after_request
    def add_headers_and_log(response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            # Injection d'en-têtes HTTP de performance et de traçabilité
            response.headers["X-Response-Time-Seconds"] = f"{elapsed:.4f}"
        return response

    # --- 2. GESTION CENTRALISÉE DES ERREURS ---
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Ressource introuvable", "status": 404}), 404

    @app.errorhandler(400)
    def handle_400(e):
        return jsonify({"error": "Requête invalide", "details": str(e), "status": 400}), 400

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Erreur interne du serveur", "status": 500}), 500

    @app.get('/health')
    def health():
        """Vérifier la disponibilité de l'API
        ---
        responses:
          200:
            description: API disponible
        """
        return jsonify({"status": "ok"}), 200

    app.register_blueprint(system_bp)
    return app


def migrate_user_columns():
    columns = {column['name'] for column in inspect(db.engine).get_columns('users')}
    additions = {
        'first_name': 'VARCHAR(80)',
        'last_name': 'VARCHAR(80)',
        'phone': 'VARCHAR(30)',
        'job_title': 'VARCHAR(120)',
        'skills': 'TEXT',
    }
    with db.engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f'ALTER TABLE users ADD COLUMN {name} {definition}'))