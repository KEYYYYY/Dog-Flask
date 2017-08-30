from flask import redirect, url_for, flash, request, session
from flask import Blueprint, render_template
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from flask_login import current_user

from app.auth.forms import LoginForm, RegisterForm
from app.auth.modles import User
from app import login_manager
from app import db, mail

auth = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    """加载用户的回调方法"""
    return User.query.get(int(user_id))


def send_email(to, subject, template, **kwargs):
    msg = Message('(__玩蛇社区__)' + subject, recipients=[to])
    msg.html = render_template(template, **kwargs)
    mail.send(msg)


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.verify_password(login_form.password.data):
            login_user(user)
            flash('登陆成功')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home.index'))
        flash('帐户名或密码错误')
    return render_template('login.html', login_form=login_form)


@auth.route('/register/', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user = User(
            email=register_form.email.data,
            password=register_form.password.data
        )
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(to=user.email, subject='请激活您的帐号', template='confirm.html', token=token)
        flash('注册成功，已经向你的邮箱发送了一封激活邮件，请您查收')
        return redirect(url_for('home.index'))
    return render_template('register.html', register_form=register_form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('你已经激活过，无需重复激活')
    if current_user.confirm(token):
        flash('谢谢你加入我们')
    else:
        flash('链接失效')
    return redirect(url_for('home.index'))


@auth.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('登出成功')
    return redirect(url_for('auth.login'))