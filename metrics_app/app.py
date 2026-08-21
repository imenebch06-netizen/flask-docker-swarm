import socket
import os
import psutil
import requests
from flask import Flask, jsonify
from flasgger import Swagger

app = Flask(__name__)
Swagger(app, template={
    "swagger": "2.0",
    "info": {"title": "CV Swarm Metrics API", "version": "1.0.0"}
})

@app.route('/api/v1/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Consulter les métriques et les utilisateurs
    ---
    responses:
      200:
        description: Métriques du conteneur et utilisateurs
    """
    # UC_Metrics : CPU/RAM
    metrics = {
        "container_id": socket.gethostname(),
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "memory_mb": f"{round(psutil.Process().memory_info().rss / (1024 * 1024), 2)} MB"
    }
    
    # UC_ListUsers : Récupération des utilisateurs depuis api-service
    users = []
    try:
        api_url = os.getenv('API_URL', 'http://api:5000')
        resp = requests.get(f'{api_url}/api/v1/users', timeout=2)
        if resp.status_code == 200:
            users = resp.json()
    except Exception:
        users = ["api-service indisponible"]

    return jsonify({
        "telemetry": metrics,
        "total_users": len(users) if isinstance(users, list) else 0,
        "users_list": users
    }), 200

@app.get('/health')
def health():
    """Vérifier la disponibilité du service métriques
    ---
    responses:
      200:
        description: Service disponible
    """
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)