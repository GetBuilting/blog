from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        errors = []
        if not username or len(username) < 2:
            errors.append('用户名至少 2 个字符。')
        if not email or '@' not in email:
            errors.append('请输入有效的邮箱地址。')
        if len(password) < 6:
            errors.append('密码至少 6 个字符。')
        if password != password2:
            errors.append('两次密码输入不一致。')
        if User.query.filter_by(username=username).first():
            errors.append('用户名已被注册。')
        if User.query.filter_by(email=email).first():
            errors.append('邮箱已被注册。')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录。', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(next_page or url_for('blog.index'))
        else:
            flash('用户名或密码错误。', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录。', 'info')
    return redirect(url_for('blog.index'))
