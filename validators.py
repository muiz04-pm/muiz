
import re

# Логин: только латинские буквы и цифры (без пробелов и спецсимволов)
LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9]+$")

# Пароль: только символы английской раскладки (без пробелов и кириллицы)
PASSWORD_PATTERN = re.compile(r"^[\x21-\x7E]+$")


def validate_login(login):
    """Проверяет логин. Возвращает текст ошибки или None, если всё верно."""
    if not login:
        return "Логин не должен быть пустым"
    if " " in login:
        return "Логин не должен содержать пробелы"
    if not LOGIN_PATTERN.match(login):
        return "Логин: только латинские буквы и цифры, без спецсимволов"
    return None


def validate_password(password):
    """Проверяет пароль. Возвращает текст ошибки или None."""
    if not password:
        return "Пароль не должен быть пустым"
    if " " in password:
        return "Пароль не должен содержать пробелы"
    if not PASSWORD_PATTERN.match(password):
        return "Пароль: только символы английской раскладки"
    return None


def validate_registration(login, password, confirm):
    """Полная проверка формы регистрации."""
    error = validate_login(login)
    if error:
        return error

    error = validate_password(password)
    if error:
        return error

    if not confirm:
        return "Подтвердите пароль"
    if password != confirm:
        return "Пароли не совпадают"
    return None


def validate_auth(login, password):
    """Проверка формы входа: поля не должны быть пустыми."""
    if not login:
        return "Введите логин"
    if not password:
        return "Введите пароль"
    return None