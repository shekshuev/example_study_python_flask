from flask import Flask, render_template, request, session, redirect
from data.repository import get_repository, RepositoryException
from data.dto.account_dto import AccountDTO
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from data.models.account_login_state import AccountLoginState
from functools import wraps


app = Flask(__name__)
app.secret_key = "secret_key"
login_manager = LoginManager(app)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "admin":
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def anonym_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_anonymous:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def account_state_loader(account_id: str):
    account = get_repository().get_account_by_id(int(account_id), account_id)
    return AccountLoginState(account)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", title="Главная")


@app.route("/audit", methods=["GET"])
@login_required
@admin_required
def audit():
    try:
        logs = get_repository().get_logs()
        return render_template("audit.html", title="Аудит", logs=logs)
    except RepositoryException:
        return render_template("audit.html", title="Аудит", logs=[])


@app.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
@anonym_only
def login():
    error = None
    if request.method == "POST":
        try:
            account = get_repository().get_account_by_username_and_password(
                request.form["username"], request.form["password"])
            account_state = AccountLoginState(account)
            login_user(account_state)
            return redirect("/profile")
        except RepositoryException as e:
            error = str(e)
    return render_template("login.html", title="Вход в систему", error=error)


@app.route("/accounts", methods=["GET"])
@login_required
@admin_required
def accounts():
    try:
        accounts = get_repository().get_all_accounts(current_user.id)
        success = session.pop(
            "success") if "success" in session.keys() else None
        error = session.pop("error") if "error" in session.keys() else None
        return render_template("accounts.html", title="Управление пользователями",
                               accounts=accounts,
                               success=success,
                               error=error)
    except RepositoryException as e:
        return render_template("accounts.html", title="Управление пользователями", error=str(e))


@app.route("/accounts", methods=["POST"])
@login_required
@admin_required
def create_account():
    try:
        if request.form.get("password") != request.form.get("confirm-password"):
            raise ValueError("Пароли не совпадают!")
        if len(request.form.get("password")) < 6:
            raise ValueError("Длина пароля должна быть не меньше 6 символов!")
        if len(request.form.get("username")) < 5:
            raise ValueError(
                "Длина имени пользователя должна быть не меньше 5 символов!")
        if request.form.get("role") not in ["admin", "user"]:
            raise ValueError("Неверно указана роль пользователя!")
        account = AccountDTO(username=request.form.get("username"),
                             firstname=request.form.get("firstname"),
                             lastname=request.form.get("lastname"),
                             middlename=request.form.get("middlename"),
                             password=request.form.get("password"),
                             role=request.form.get("role"))
        get_repository().create_account(account, current_user.id)
        session["success"] = "Пользователь добавлен"
        return redirect("/accounts")
    except (RepositoryException, ValueError) as e:
        session["error"] = str(e)
        return redirect("/accounts")


@app.route("/accounts/delete", methods=["POST"])
@login_required
@admin_required
def delete_account():
    try:
        get_repository().delete_account_by_id(
            int(request.form.get("id")), current_user.id)
        session["success"] = "Пользователь удален"
        return redirect("/accounts")
    except (RepositoryException, ValueError, TypeError) as e:
        session["error"] = str(e)
        return redirect("/accounts")


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    try:
        account = get_repository().get_account_by_id(
            int(current_user.id), current_user.id)
        success = session.pop(
            "success") if "success" in session.keys() else None
        error = session.pop("error") if "error" in session.keys() else None
        return render_template("profile.html", title="Личный кабинет", account=account, success=success, error=error)
    except RepositoryException as e:
        return render_template("profile.html", title="Личный кабинет", error=str(e))


@app.route("/accounts/edit", methods=["POST"])
@login_required
def edit_account():
    try:
        if request.form.get("password") != request.form.get("confirm-password"):
            raise ValueError("Пароли не совпадают!")
        if len(request.form.get("password")) < 6:
            raise ValueError("Длина пароля должна быть не меньше 6 символов!")
        if len(request.form.get("username")) < 5:
            raise ValueError(
                "Длина имени пользователя должна быть не меньше 5 символов!")
        account = AccountDTO(username=request.form.get("username"),
                             firstname=request.form.get("firstname"),
                             lastname=request.form.get("lastname"),
                             middlename=request.form.get("middlename"),
                             password=request.form.get("password"),
                             role=current_user.role)
        account_id = int(request.form.get("id"))
        if account_id == current_user.id:
            get_repository().update_account(account_id, account, current_user.id)
            session["success"] = "Пользователь изменен"
            return redirect("/profile")
        else:
            raise ValueError("Пользователь может изменить только свои данные!")
    except (RepositoryException, ValueError, TypeError) as e:
        session["error"] = str(e)
        return redirect("/profile")
