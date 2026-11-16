import psycopg2
from psycopg2 import extras, errors
import bcrypt

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "auth_app",
    "user": "postgres",
    "password": "",
}


def get_connection():
    """Создаёт и возвращает соединение с БД."""
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Создаёт таблицу users и пробные аккаунты (admin/user), если их нет."""
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            login VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(100) NOT NULL,
            role VARCHAR(10) NOT NULL DEFAULT 'user'
                CHECK (role IN ('user', 'admin'))
        );
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
    finally:
        conn.close()

    # Пробные аккаунты: создаются только один раз
    test_accounts = (
        ("admin", "admin123", "admin"),
        ("user", "user123", "user"),
    )
    for login, password, role in test_accounts:
        if get_user(login) is None:
            create_user(login, password, role)


def get_user(login):
    """Возвращает пользователя по логину (словарь) или None, если не найден."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            # Параметризованный запрос — защита от SQL-инъекций
            cur.execute(
                "SELECT id, login, password_hash, role FROM users WHERE login = %s",
                (login,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def create_user(login, password, role="user"):
    """
    Регистрирует пользователя: хеширует пароль bcrypt и сохраняет в БД.
    Возвращает True при успехе, False — если логин уже занят.
    """
    # Хешируем пароль: bcrypt сам генерирует соль
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (login, password_hash, role) VALUES (%s, %s, %s)",
                (login, password_hash, role),
            )
        conn.commit()
        return True
    except errors.UniqueViolation:
        # Сработало ограничение UNIQUE на поле login
        return False
    finally:
        conn.close()


def get_all_users():
    """Возвращает список всех пользователей (без хешей паролей — их показывать нельзя)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT id, login, role FROM users ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()