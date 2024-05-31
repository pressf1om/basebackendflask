import re
import os
import sqlalchemy
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import redirect
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import itsdangerous
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import json
from flask_restful import Api, Resource


# app config
app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basebackend.db'
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)


# class user for db
class User(db.Model, UserMixin):
    # айди юзера
    id = db.Column(db.Integer, primary_key=True)
    # почта
    email = db.Column(db.String(200), nullable=False)
    # логин
    username = db.Column(db.String(120), nullable=False, unique=True)
    # пароль
    password = db.Column(db.String(120), nullable=False)
    # дата регистрации
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    # статус пользователя в общей иерархии юзеров
    status = db.Column(db.String(120), default='Пользователь')


# авторизация
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


# главная страница
@app.route('/', methods=['POST', 'GET'])
def home():
    # Создаем все таблицы базы данных
    db.create_all()

    # Проверяем, есть ли пользователь "admin" в базе данных
    admin_user = User.query.filter_by(username='admin').first()

    # Если пользователь "admin" отсутствует, создаем его
    if not admin_user:
        # Создаем пользователя "admin" с паролем "12345"
        admin = User(username='admin', password='12345', email='admin@example.com', status='Администратор')

        # Добавляем пользователя в базу данных
        db.session.add(admin)
        db.session.commit()
        print("Пользователь 'admin' создан.")

    return render_template("home.html")


# about
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template("about.html")


# профиль пользователя
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # получаем айди пользователя зашедшего на страницу
    user_id = current_user.id

    # получаем объект пользователя из базы данных по его идентификатору
    user = db.session.get(User, user_id)

    # если запрос метода POST, значит пользователь отправил форму для обновления профиля
    if request.method == 'POST':
        # получаем данные из формы
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # обновляем данные профиля пользователя
        user.username = username
        user.email = email
        user.password = password

        # сохраняем изменения в базе данных
        db.session.commit()

        # перенаправляем пользователя на страницу его профиля
        return redirect('/account')

    # рендерим страницу профиля с текущими данными пользователя
    return render_template("account.html", data=user.__dict__)


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == "POST":
        # получение данных из формы
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # собираем объект юзер_ для регистрации в бд
        user_ = User(username=username, password=password, email=email)

        # регистрация в базе
        db.session.add(user_)
        db.session.commit()

        return redirect("/")
    else:
        return render_template("registration.html")


# Вход
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "GET":
        return render_template('login.html')

    login_form = request.form.get('username')
    password_form = request.form.get('password')

    if login_form and password_form:
        user_auth = User.query.filter_by(username=login_form).first()

        if user_auth and user_auth.password == password_form:
            login_user(user_auth)
            return redirect("/")

        error_message = 'Логин либо пароль не совпадают с базой'
        return render_template('error.html', error_message=error_message)

    error_message = 'Недостаточно данных для авторизации'
    return render_template('error.html', error_message=error_message)


# посмотреть всех пользвателей
@app.route("/admin/print_users", methods=['GET', 'POST'])
@login_required
def print_user():
    # получаем айди пользователя зашедшего на сайт
    user_id = current_user.id

    # забираем инфу из бд по нему
    user_status = User.query.filter_by(id=user_id).first()

    # разграничение прав доступа
    if user_status.status == 'Администратор':
        if request.method == 'POST':
            # получаем данные из формы
            user_id_to_update = request.form.get('user_id')
            new_status = request.form.get('status')

            # обновляем статус пользователя в базе данных
            user_to_update = db.session.get(User, user_id_to_update)
            user_to_update.status = new_status
            db.session.commit()

        # получаем список всех пользователей
        user_print = User.query.order_by(User.id).all()
        return render_template("print_user.html", data=user_print)
    else:
        error_message = 'У вас недостаточно прав'
        return render_template('error.html', error_message=error_message)


# выход
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # деаутендификация через фласк логин
    logout_user()
    return redirect("/")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', error=error), 404


class API(Resource):
    def get(self):
        pass

    def post(self):
        pass


# Добавление ресурса к API
api.add_resource(API, '/api')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=port)




