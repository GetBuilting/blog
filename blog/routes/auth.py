import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Photo

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


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action', '')

        # 修改昵称
        if action == 'nickname':
            nickname = request.form.get('nickname', '').strip()
            if not nickname:
                flash('昵称不能为空。', 'error')
            else:
                current_user.nickname = nickname
                db.session.commit()
                flash('昵称修改成功！', 'success')

        # 修改头像
        elif action == 'avatar':
            avatar = request.form.get('avatar', '').strip()
            if avatar:
                current_user.avatar = avatar
                db.session.commit()
                flash('头像修改成功！', 'success')

        # 修改密码
        elif action == 'password':
            old_pw = request.form.get('old_password', '')
            new_pw = request.form.get('new_password', '')
            new_pw2 = request.form.get('new_password2', '')

            if not current_user.check_password(old_pw):
                flash('原密码错误。', 'error')
            elif len(new_pw) < 6:
                flash('新密码至少 6 个字符。', 'error')
            elif new_pw != new_pw2:
                flash('两次新密码输入不一致。', 'error')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('密码修改成功！', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


@auth_bp.route('/album')
@login_required
def album():
    photos = current_user.photos.order_by(Photo.created_at.desc()).all()
    return render_template('auth/album.html', photos=photos)


@auth_bp.route('/album/upload', methods=['POST'])
@login_required
def album_upload():
    # 检查限额
    count = current_user.photos.count()
    if count >= 10:
        flash('相册已满！最多上传 10 张图片，请先删除旧图片。', 'error')
        return redirect(url_for('auth.album'))

    file = request.files.get('photo')
    if not file or file.filename == '':
        flash('请选择图片。', 'error')
        return redirect(url_for('auth.album'))

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
        flash('仅支持 png/jpg/jpeg/gif/webp 格式。', 'error')
        return redirect(url_for('auth.album'))

    filename = f'{uuid.uuid4().hex}.{ext}'
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'photos')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    photo = Photo(user_id=current_user.id, filename=filename, original_name=file.filename)
    db.session.add(photo)
    db.session.commit()
    flash('图片上传成功！', 'success')
    return redirect(url_for('auth.album'))


@auth_bp.route('/album/delete/<int:photo_id>', methods=['POST'])
@login_required
def album_delete(photo_id):
    photo = db.session.get(Photo, photo_id)
    if not photo or photo.user_id != current_user.id:
        flash('图片不存在。', 'error')
        return redirect(url_for('auth.album'))

    # Delete file
    filepath = os.path.join(current_app.static_folder, 'uploads', 'photos', photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(photo)
    db.session.commit()
    flash('图片已删除。', 'info')
    return redirect(url_for('auth.album'))
