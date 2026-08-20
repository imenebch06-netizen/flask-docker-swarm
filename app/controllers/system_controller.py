from flask import Blueprint, jsonify
from app.services.system_service import SystemService

system_bp = Blueprint('system', __name__)

@system_bp.route('/api/v1/info', methods=['GET'])
def get_info():
    """Identifie le conteneur actif dans le cluster Swarm.
    ---
    responses:
      200:
        description: Identifiant du conteneur exécutant la requête
    """
    data = SystemService.get_node_info()
    return jsonify(data), 200