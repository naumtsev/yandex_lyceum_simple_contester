#!/usr/bin/python
# -*- coding: utf-8 -*-



from flask import Flask, render_template, request, redirect, session
import json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, SelectField
from wtforms.widgets import TextArea, TextInput
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e70lIUUoXRKlXc5VUBmiJ9Hdi'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMINS = json.loads(open('static/admins.txt', 'r', encoding='utf-8').read())

class LoginForm(FlaskForm):
    user_name = StringField('Login:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Войти')

class AddSolveForm(FlaskForm):
    task_name = StringField('Название задачи:', validators=[DataRequired()], widget=TextInput())
    code = TextAreaField('Код:', validators=[DataRequired()],widget=TextArea())
    submit = SubmitField('Отправить')

class RegisterForm(FlaskForm):
    user_name = StringField('Username:', validators=[DataRequired()])
    password = StringField('Password:', validators=[DataRequired()])
    email = StringField('Email:', validators=[Email()])
    name = StringField('Name:', validators=[DataRequired()])
    surname = StringField('Surname:', validators=[DataRequired()])
    submit = SubmitField('Отправить')

class SelectStatus(FlaskForm):
    select = SelectField('Выберите статус',choices=[('На проверке', 'На проверке'), ('Отклонено', 'Отклонено'), ('Зачтено', 'Зачтено')])
    submit = SubmitField('Сохранить')


db = SQLAlchemy(app)

class YandexLyceumStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return '<YandexLyceumStudent {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname)

class SolutionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120), unique=False, nullable=False)
    code = db.Column(db.String(2000), unique=False, nullable=False)
    status = db.Column(db.String(50), unique=False, nullable=False)
    student_id = db.Column(db.Integer,
                           db.ForeignKey('yandex_lyceum_student.id'),
                           nullable=False)
    student = db.relationship('YandexLyceumStudent',
                              backref=db.backref('SolutionAttempts',
                                                 lazy=True))

    def __repr__(self):
        return '<SolutionAttempt {} {} {}>'.format(
            self.id, self.task, self.status)



class AnnouncementModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(80), unique=False, nullable=False)
    title = db.Column(db.String(200), unique=False, nullable=False)
    announcement = db.Column(db.String(2000), unique=True, nullable=False)

    def __repr__(self):
        return '<AnnouncementModel {} {} {}>'.format(
            self.id, self.author, self.title)


db.create_all()



@app.route('/delete_solution/<id>', methods=['POST', 'GET'])
def delete_solution(id):
    if 'user' in session:
        return redirect('/')

    solution = SolutionAttempt.query.filter_by(id=id).first()
    user = solution.student
    if user.id == solution.student_id or session['username'] in ADMINS:
        db.session.delete(solution)
        db.session.commit()

    if session['username'] in ADMINS:
        return redirect('/solutions')
    else:
        return redirect('/my_solutions')






@app.route('/delete_announcement_<id>', methods=['POST', 'GET'])
def delete_announcement(id):
    if 'username' not in session:
        return redirect('/')

    if session['username'] not in ADMINS:
        return redirect('/')

    me = AnnouncementModel.query.filter_by(id=id).first()
    db.session.delete(me)
    db.session.commit()
    return redirect('/')


@app.route('/add_announcement', methods=['POST', 'GET'])
def ad_announcement():
    if 'username' not in session:
        return redirect('/')

    if session['username'] not in ADMINS:
        return redirect('/')

    form = AddSolveForm()
    if form.validate_on_submit():
        code = form.code.data
        task_name = form.task_name.data
        event = AnnouncementModel(author=session["username"],
                                     title=task_name,
                                     announcement=code)
        db.session.add(event)
        db.session.commit()
        return redirect('/')
    return render_template("add_announcement.html", ADMINS=ADMINS, session=session, form=form)




@app.route('/', methods=['POST', 'GET'])
def index():
    if 'username' not in session:
        return redirect('/login')
    all = AnnouncementModel.query.all()
    announcements = []
    for i in all:
        announcements.append((i.id, i.author, i.title, i.announcement))
    return render_template('index.html', ADMINS=ADMINS, session=session, events=announcements, sz=len(announcements))


@app.route('/logout')
def logout():
    session.pop('username',0)
    return redirect('/login')


@app.route('/solutions')
def solutions():
    if 'username' not in session:
        return redirect('/login')

    if session['username'] not in ADMINS:
        return redirect('/')

    all = SolutionAttempt.query.all()
    arr = []
    for i in all:
        id = i.id
        sender = i.student.username
        task = i.task
        status = i.status
        arr.append((id, sender, task, status))
    return render_template('admin_solutions.html', session=session, ADMINS=ADMINS, solutions=arr, sz=len(arr))


@app.route('/my_solutions', methods=['POST', 'GET'])
def my_solutions():
    if 'username' not in session:
        return redirect('/login')
    user = YandexLyceumStudent.query.filter_by(username=session['username']).first()
    all = SolutionAttempt.query.filter_by(student_id=user.id)
    arr = []
    for i in all:
        arr.append((i.id, i.task, i.status))
    return render_template('my_solutions.html', ADMINS=ADMINS, session=session, solutions=arr, sz=len(arr))

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.user_name.data
        password = form.password.data
        user = YandexLyceumStudent.query.filter_by(username=user_name)
        try:
            if(user.first().password == password):
                    user = user.first()
                    session['username'] = user.username
                    return redirect('/')
            else:
                return render_template('login.html', form=form, session=session, status=3)
        except Exception:
            return render_template('login.html', form=form, session=session, status=3)
    return render_template('login.html', form=form, session=session, status=1)



@app.route('/change_status/<id>', methods=['POST', 'GET'])
def change_status(id):
    if 'username' not in session:
        return redirect('/')

    if session['username'] not in ADMINS:
        return redirect('/')

    solve = SolutionAttempt.query.filter_by(id=id).first()
    user = YandexLyceumStudent.query.filter_by(id=solve.student_id).first()
    form = SelectStatus()

    if form.validate_on_submit():
        solve.status = form.select.data
        db.session.commit()
        return redirect('/solutions')
    return render_template('change_status.html',session=session, ADMINS=ADMINS, form=form, code=solve.code, id=user.id, username=user.username, task=solve.task)


@app.route('/code/<id>', methods=['POST', 'GET'])
def code_(id):
    if 'username' not in session:
        return redirect('/')

    solve = SolutionAttempt.query.filter_by(id=id).first()
    user = YandexLyceumStudent.query.filter_by(id=solve.student_id).first()
    if user.username == session['username'] or session['username'] in ADMINS:
        return render_template('base.html', code = solve.code, ADMINS=ADMINS, session=session, task_name=solve.task)
    else:
        return redirect('/')


@app.route('/send_solution', methods=['POST', 'GET'])
def send_solution():
    if 'username' not in session:
        return redirect('/login')

    form = AddSolveForm()
    if form.validate_on_submit():
        code = form.code.data
        task_name = form.task_name.data
        solution = SolutionAttempt( task = task_name,
                                    code = code,
                                    status = 'На проверке'
                                    )
        print(code)
        user = YandexLyceumStudent.query.filter_by(username=session['username']).first()
        user.SolutionAttempts.append(solution)
        db.session.commit()
        return redirect('/my_solutions')
    return render_template('add.html', ADMINS=ADMINS, session=session, form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'user' in session:
        return redirect('/')

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.user_name.data
        password = form.password.data
        email = form.email.data
        name = form.name.data
        surname = form.surname.data

        flag = YandexLyceumStudent.query.filter_by(username=username).first()

        if (not flag and username not in ADMINS):
            user = YandexLyceumStudent(username=username,
                                       password=password,
                                email=email,
                                name=name,
                                surname=surname)
            session['username'] = username
            db.session.add(user)
            db.session.commit()
            return redirect("/")
        else:
            return render_template('register.html', form=form, status=3)

    return render_template('register.html', form=form, session=session)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('error404.html'), 404



DEBUG = True
if DEBUG:
    if __name__ == '__main__':
        app.run(port=8080, host='127.0.0.1')