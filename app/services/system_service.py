import socket
from sqlalchemy.exc import IntegrityError
from app.models.user import db, User
from app.celery_utils import celery_app


class DuplicateEmailError(Exception):
    """Levée lorsque l'email fourni est déjà utilisé par un autre candidat."""


class SystemService:
    @staticmethod
    def get_container_id():
        return socket.gethostname()

    @staticmethod
    def create_cv_request(data):
        first_name = data.get('first_name') or data.get('username', '')
        last_name = data.get('last_name', '')
        container_id = SystemService.get_container_id()
        user = User(
            username=data.get('username') or first_name,
            first_name=first_name,
            last_name=last_name,
            email=data.get('email'),
            phone=data.get('phone', ''),
            job_title=data.get('job_title', ''),
            experiences=data.get('experiences', ''),
            skills=data.get('skills', ''),
            theme_color=data.get('theme_color', '#2C3E50'),
            pdf_status="PENDING",
            processed_by_container=container_id
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            # L'email est contraint unique en base : sans ce filet, une
            # double soumission (ou un doublon) faisait planter la requête
            # avec une erreur 500 brute au lieu d'un message exploitable.
            db.session.rollback()
            raise DuplicateEmailError(data.get('email'))

        celery_app.send_task("compile_pdf_task", args=[user.id, user.to_dict()])

        return user.to_dict()

    @staticmethod
    def get_user_status(user_id):
        user = db.session.get(User, user_id)
        return user.to_dict() if user else None

    @staticmethod
    def get_all_users():
        return [u.to_dict() for u in User.query.all()]