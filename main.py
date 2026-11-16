import tkinter as tk
from tkinter import ttk, messagebox

import bcrypt
import psycopg2

import database as db
import validators


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Авторизация")
        self.geometry("400x370")
        self.resizable(False, False)

        self.current_user = None  # данные вошедшего пользователя
        self._build_ui()
        self.login_entry.focus_set()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------- Вкладка «Вход» ----------
        login_frame = ttk.Frame(notebook, padding=15)
        notebook.add(login_frame, text="Вход")

        ttk.Label(login_frame, text="Логин:").pack(anchor="w")
        self.login_entry = ttk.Entry(login_frame)
        self.login_entry.pack(fill="x", pady=(0, 10))

        ttk.Label(login_frame, text="Пароль:").pack(anchor="w")
        self.login_password = ttk.Entry(login_frame, show="*")
        self.login_password.pack(fill="x", pady=(0, 10))
        self.login_password.bind("<Return>", lambda event: self.on_login())

        self.login_error = ttk.Label(
            login_frame, text="", foreground="red", wraplength=330
        )
        self.login_error.pack(anchor="w")

        ttk.Button(login_frame, text="Войти", command=self.on_login).pack(
            fill="x", pady=(10, 0)
        )

        reg_frame = ttk.Frame(notebook, padding=15)
        notebook.add(reg_frame, text="Регистрация")

        ttk.Label(reg_frame, text="Логин:").pack(anchor="w")
        self.reg_login = ttk.Entry(reg_frame)
        self.reg_login.pack(fill="x", pady=(0, 10))

        ttk.Label(reg_frame, text="Пароль:").pack(anchor="w")
        self.reg_password = ttk.Entry(reg_frame, show="*")
        self.reg_password.pack(fill="x", pady=(0, 10))

        ttk.Label(reg_frame, text="Повторите пароль:").pack(anchor="w")
        self.reg_confirm = ttk.Entry(reg_frame, show="*")
        self.reg_confirm.pack(fill="x", pady=(0, 10))
        self.reg_confirm.bind("<Return>", lambda event: self.on_register())

        self.reg_error = ttk.Label(
            reg_frame, text="", foreground="red", wraplength=330
        )
        self.reg_error.pack(anchor="w")

        ttk.Button(reg_frame, text="Зарегистрироваться", command=self.on_register).pack(
            fill="x", pady=(10, 0)
        )

    # ---------- Обработчики ----------

    def on_login(self):
        """Вход: проверка полей, поиск пользователя в БД, сверка пароля с хешем."""
        login = self.login_entry.get()
        password = self.login_password.get()

        error = validators.validate_auth(login, password)
        if error:
            self.login_error.config(text=error)
            return

        try:
            user = db.get_user(login)
        except psycopg2.Error:
            self.login_error.config(text="Ошибка подключения к базе данных")
            return

        # Вход только если пользователь есть в БД И пароль совпадает с хешем.
        # Сообщение одинаковое для обоих случаев — не подсказываем, что именно неверно.
        if user is None or not bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        ):
            self.login_error.config(text="Неверный логин или пароль")
            return

        self.login_error.config(text="")
        self.current_user = user
        self._clear_fields()
        self.withdraw()  # скрываем окно авторизации

        # Открываем окно в зависимости от роли
        if user["role"] == "admin":
            AdminWindow(self)
        else:
            UserWindow(self)

    def on_register(self):
        """Регистрация: валидация, хеширование пароля, запись в БД."""
        login = self.reg_login.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()

        error = validators.validate_registration(login, password, confirm)
        if error:
            self.reg_error.config(text=error)
            return

        try:
            # Новые пользователи всегда получают роль 'user'
            created = db.create_user(login, password)
        except psycopg2.Error:
            self.reg_error.config(text="Ошибка подключения к базе данных")
            return

        if not created:
            self.reg_error.config(text="Пользователь с таким логином уже существует")
            return

        self.reg_error.config(text="")
        self.reg_login.delete(0, "end")
        self.reg_password.delete(0, "end")
        self.reg_confirm.delete(0, "end")
        messagebox.showinfo(
            "Регистрация", f"Пользователь «{login}» успешно зарегистрирован!"
        )

    def logout(self):
        """Выход из аккаунта: возврат к окну авторизации."""
        self.current_user = None
        self.deiconify()

    def _clear_fields(self):
        self.login_entry.delete(0, "end")
        self.login_password.delete(0, "end")


class UserWindow(tk.Toplevel):
    """Окно обычного пользователя."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Личный кабинет")
        self.geometry("350x180")
        self.resizable(False, False)

        user = app.current_user
        ttk.Label(
            self, text=f"Добро пожаловать, {user['login']}!",
            font=("Arial", 13, "bold"),
        ).pack(pady=(25, 5))
        ttk.Label(self, text=f"Ваша роль: {user['role']}").pack(pady=5)
        ttk.Button(self, text="Выйти", command=self.on_logout).pack(pady=20)

        # Закрытие окна крестиком = выход из аккаунта
        self.protocol("WM_DELETE_WINDOW", self.on_logout)

    def on_logout(self):
        self.destroy()
        self.app.logout()


class AdminWindow(tk.Toplevel):
    """Окно администратора: список всех пользователей системы."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Панель администратора")
        self.geometry("520x360")
        self.minsize(400, 250)

        ttk.Label(
            self, text=f"Администратор: {app.current_user['login']}",
            font=("Arial", 12, "bold"),
        ).pack(pady=10)

        columns = ("id", "login", "role")
        self.table = ttk.Treeview(self, columns=columns, show="headings")
        self.table.heading("id", text="ID")
        self.table.heading("login", text="Логин")
        self.table.heading("role", text="Роль")
        self.table.column("id", width=50, anchor="center")
        self.table.column("login", width=250, anchor="w")
        self.table.column("role", width=100, anchor="center")
        self.table.pack(fill="both", expand=True, padx=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Обновить", command=self.load_users).pack(side="left")
        ttk.Button(btn_frame, text="Выйти", command=self.on_logout).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self.on_logout)
        self.load_users()

    def load_users(self):
        """Загружает всех пользователей из БД в таблицу."""
        try:
            users = db.get_all_users()
        except psycopg2.Error:
            messagebox.showerror("Ошибка", "Не удалось загрузить пользователей из БД")
            return

        self.table.delete(*self.table.get_children())
        for u in users:
            self.table.insert("", "end", values=(u["id"], u["login"], u["role"]))

    def on_logout(self):
        self.destroy()
        self.app.logout()


if __name__ == "__main__":
    try:
        db.init_db()
    except psycopg2.Error as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка БД",
            "Не удалось подключиться к PostgreSQL.\n"
            "Проверьте параметры в файле database.py",
        )
        root.destroy()
        raise SystemExit(1)

    app = App()
    app.mainloop()