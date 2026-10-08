"""User registration and persistence services."""

import logging
from datetime import datetime, timezone

from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database.mongodb import MongoDBUnavailable, mongodb
from app.models.user import User


logger = logging.getLogger(__name__)
password_hash = PasswordHash.recommended()


class DuplicateUserError(Exception):
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"{field.capitalize()} is already registered.")


class UserStoreUnavailable(Exception):
    """Raised when user data cannot safely be read or written."""


RegistrationUnavailable = UserStoreUnavailable


def hash_password(password: str) -> str:
    """Return a salted Argon2id password hash."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify against the same Argon2 password hasher used at registration."""
    try:
        return password_hash.verify(password, hashed_password)
    except Exception:
        return False


DUMMY_PASSWORD_HASH = hash_password("dummy-password-used-for-timing-only")


class AuthService:
    def __init__(self) -> None:
        self._indexes_ready = False

    def _users(self):
        if mongodb.database is None:
            raise RegistrationUnavailable("MongoDB is not connected.")
        return mongodb.database["users"]

    async def ensure_indexes(self) -> None:
        """Enforce case-normalized email and username uniqueness in MongoDB."""
        users = self._users()
        try:
            await users.create_index("email", unique=True, name="uniq_users_email")
            await users.create_index(
                "username", unique=True, name="uniq_users_username"
            )
        except PyMongoError as exc:
            self._indexes_ready = False
            logger.error("Could not initialize user uniqueness indexes.")
            raise RegistrationUnavailable(
                "User registration storage is unavailable."
            ) from exc
        self._indexes_ready = True

    async def register_user(
        self, *, email: str, username: str, hashed_password: str
    ) -> User:
        users = self._users()
        if not self._indexes_ready:
            await self.ensure_indexes()

        try:
            if await users.find_one({"email": email}, {"_id": 1}):
                raise DuplicateUserError("email")
            if await users.find_one({"username": username}, {"_id": 1}):
                raise DuplicateUserError("username")

            now = datetime.now(timezone.utc)
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                created_at=now,
                updated_at=now,
            )
            await users.insert_one(user.to_mongo_document())
            return user
        except DuplicateUserError:
            raise
        except DuplicateKeyError as exc:
            key_pattern = (exc.details or {}).get("keyPattern", {})
            duplicate_field = "username" if "username" in key_pattern else "email"
            raise DuplicateUserError(duplicate_field) from exc
        except (PyMongoError, MongoDBUnavailable) as exc:
            raise RegistrationUnavailable(
                "User registration storage is unavailable."
            ) from exc

    async def get_user_by_identifier(self, identifier: str) -> User | None:
        """Look up a user by their normalized email address or username."""
        users = self._users()
        normalized = identifier.strip().lower()
        try:
            document = await users.find_one(
                {"$or": [{"email": normalized}, {"username": normalized}]}
            )
        except PyMongoError as exc:
            raise UserStoreUnavailable("User lookup is unavailable.") from exc
        return User.from_mongo_document(document) if document else None

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Look up a token subject by MongoDB ObjectId."""
        from bson import ObjectId

        if not ObjectId.is_valid(user_id):
            return None
        try:
            document = await self._users().find_one({"_id": ObjectId(user_id)})
        except PyMongoError as exc:
            raise UserStoreUnavailable("User lookup is unavailable.") from exc
        return User.from_mongo_document(document) if document else None


auth_service = AuthService()
