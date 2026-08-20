import socket

class SystemService:
    @staticmethod
    def get_node_info():
        return {
            "container_id": socket.gethostname(),
            "status": "Healthy",
            "message": "Reponse traitée par le cluster"
        }