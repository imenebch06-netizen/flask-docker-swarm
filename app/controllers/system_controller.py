import os
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from app.services.system_service import SystemService

system_bp = Blueprint('system', __name__)

@system_bp.route('/api/v1/cv', methods=['POST'])
def generate_cv():
    """UC_EditCV & UC_Theme & UC_GenPDF : Générer un CV ExpressPDF
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            first_name: {type: string}
            last_name: {type: string}
            username: {type: string}
            email: {type: string}
            phone: {type: string}
            job_title: {type: string}
            experiences: {type: string}
            skills: {type: string}
            theme_color: {type: string}
    responses:
      202:
        description: Traitement asynchrone lancé avec succès
    """
    payload = request.get_json() or {}
    if not payload.get('email'):
      return jsonify({"error": "Le champ email est requis"}), 400
    if not (payload.get('first_name') or payload.get('username')):
      return jsonify({"error": "Le champ first_name est requis"}), 400

    user_data = SystemService.create_cv_request(payload)
    return jsonify({
        "message": "Génération de votre PDF en cours...",
        "user": user_data
    }), 202

@system_bp.route('/api/v1/cv/<int:user_id>/status', methods=['GET'])
def check_status(user_id):
    """UC_Download : Consulter le statut de la génération
    ---
    responses:
      200:
        description: État d'avancement du PDF
    """
    user_data = SystemService.get_user_status(user_id)
    if not user_data:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    return jsonify(user_data), 200

@system_bp.route('/api/v1/cv/<int:user_id>/download', methods=['GET'])
def download_cv(user_id):
    """Télécharger le PDF généré
    ---
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    produces:
      - application/pdf
    responses:
      200:
        description: Fichier PDF du CV
      202:
        description: Génération encore en cours
      404:
        description: Utilisateur ou fichier introuvable
    """
    user_data = SystemService.get_user_status(user_id)
    if not user_data:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    if user_data['pdf_status'] == 'PENDING':
        return jsonify({"error": "PDF encore en cours de génération"}), 202
    if user_data['pdf_status'] != 'READY' or not user_data['pdf_filename']:
        return jsonify({"error": "PDF indisponible"}), 500

    pdf_directory = current_app.config['PDF_DIRECTORY']
    if not os.path.isfile(os.path.join(pdf_directory, user_data['pdf_filename'])):
        return jsonify({"error": "Fichier PDF introuvable"}), 404
    return send_from_directory(pdf_directory, user_data['pdf_filename'], as_attachment=True)

@system_bp.route('/api/v1/users', methods=['GET'])
def get_users():
    """Consulter la liste globale des utilisateurs
    ---
    responses:
      200:
        description: Liste des utilisateurs
    """
    return jsonify(SystemService.get_all_users()), 200