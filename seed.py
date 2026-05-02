from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole, UserStatus
from app.models.user import User


def upsert_user(
    db,
    *,
    email: str,
    full_name: str,
    phone: str,
    password: str,
    roles: list[UserRole],
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None:
        user = User(email=normalized_email)
        db.add(user)

    user.full_name = full_name
    user.phone = phone
    user.email = normalized_email
    user.password_hash = hash_password(password)
    user.roles = roles
    user.status = status

    return user


def seed_data() -> None:
    db = SessionLocal()
    try:
        upsert_user(
            db,
            email="daler@gmail.com",
            full_name="Daler Ismatov",
            phone="+998947668884",
            password="12345678",
            roles=[UserRole.ADMIN, UserRole.TEACHER],
        )

        upsert_user(
            db,
            email="rasulov420@gmail.com",
            full_name="Hasan Rasulov",
            phone="+998931373027",
            password="qwerty123",
            roles=[UserRole.ADMIN, UserRole.TEACHER],
        )

        upsert_user(
            db,
            email="dalerjon@gmail.com",
            full_name="Dalerjon Admin",
            phone="+998900000000",
            password="12345678d",
            roles=[UserRole.ADMIN, UserRole.TEACHER],
        )

        db.commit()

        print("Seed completed successfully.")
        print("Admin: daler@gmail.com  / 12345678")
        print("Hasan: rasulov420@gmail.com / qwerty123")
        print("Dalerjon: dalerjon@gmail.com / 12345678d")

    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
