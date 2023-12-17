import base64
import pickle
import re

from sqlalchemy.orm import Session, joinedload
from engine.recognition import FaceRecognizer
from .models import User, Face

face_recognizer: FaceRecognizer | None = None


def _encode(features: list):
    return base64.b64encode(pickle.dumps(features)).decode('utf-8')


def _decode(string):
    return pickle.loads(base64.b64decode(string))


def _normalize_username(string, separator="_"):
    new_string = re.sub(r'([A-Z])', r' \1', string).lower()
    new_string = re.sub(r'\s+', separator, new_string).strip(separator)
    new_string = re.sub(re.escape(separator) + r'+', separator, new_string)
    return new_string


def _unnormalize_username(string, separator="_"):
    return " ".join([word.title() for word in string.split(separator)])


class UserController:
    @staticmethod
    def create_user(session: Session, username: str):
        db_user = User(username=username)

        with session as db:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        return db_user

    @staticmethod
    def get_user_by_username(session: Session, username: str):
        with session as db:
            user = db.query(User).filter(User.username == username).first()
        return user

    @staticmethod
    def add_face(session: Session, user_id: int, features: str):
        db_face = Face(user_id=user_id, features=features)
        with session as db:
            db.add(db_face)
            db.commit()
            db.refresh(db_face)
        return db_face

    @staticmethod
    def get_users(session: Session, skip: int = 0, limit: int = 100):
        with session as db:
            db_users = (
                db.query(User)
                .options(joinedload(User.faces))
                .offset(skip)
                .limit(limit)
                .all()
            )

        return db_users


class EngineController:
    @staticmethod
    def load_model():
        global face_recognizer
        if face_recognizer is None:
            face_recognizer = FaceRecognizer()

    @staticmethod
    def register_face(session: Session, username: str, images: list):
        username = _normalize_username(username)

        if not username:
            return {"status": "failed", "message": "Username is not valid."}

        # Check if the user already exists
        user = UserController.get_user_by_username(session=session, username=username)

        if not user:
            # If the user doesn't exist, create a new user
            user = UserController.create_user(session=session, username=username)

        data = face_recognizer.encode(images)
        faces = []
        for features in data:
            face = UserController.add_face(
                session=session,
                user_id=user.id,
                features=_encode(features)
            )
            faces.append(face)

        return {
            "status": "success",
            "message": "Face registered successfully for user: {}".format(_unnormalize_username(username))
        }

    @staticmethod
    def recognize(session: Session, file):
        data = face_recognizer.encode(file)

        if len(data) == 0:
            return {"status": "failed", "message": "Face is not detected."}

        users = UserController.get_users(session=session)
        result = []
        for features in data:
            similar_users = []
            for user in users:
                faces = [_decode(face.features) for face in user.faces]
                is_similar, score = face_recognizer.compare(faces, features)
                if is_similar:
                    similar_users.append([_unnormalize_username(user.username), float(score)])

            if not similar_users:
                result.append(["Unknown Face", -1])
                continue

            similar_users = max(similar_users, key=lambda x: x[1])
            result.append(similar_users)

        if not result:
            return {"status": "failed", "message": "Face unknown."}

        return {"status": "success", "message": "Face recognized", "data": result}
