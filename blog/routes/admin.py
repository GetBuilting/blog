from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Article, User
from services.github_service import GitHubService
from services.article_service import (
    create_article, update_article, delete_article,
    approve_article, reject_article,
)
from flask import current_app

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限。', 'error')
            return redirect(url_for('blog.index'))
        return f(*args, **kwargs)
    return decorated


def get_gh_service():
    app = current_app
    return GitHubService(
        token=app.config.get('GITHUB_TOKEN', ''),
        repo_name=app.config.get('GITHUB_REPO', ''),
    )


def get_base_url():
    return current_app.config.get('BASE_URL', 'http://localhost:5000')


# ---- Dashboard ----
@admin_bp.route('/')
@admin_required
def dashboard():
    article_count = Article.query.count()
    published_count = Article.query.filter_by(is_published=True, review_status='approved').count()
    pending_count = Article.query.filter_by(review_status='pending').count()
    user_count = User.query.count()
    return render_template(
        'admin/dashboard.html',
        article_count=article_count,
        published_count=published_count,
        pending_count=pending_count,
        user_count=user_count,
    )


# ---- Review Queue (审核管理) ----
@admin_bp.route('/review')
@admin_required
def review():
    page = request.args.get('page', 1, type=int)
    # Only show published + pending/rejected (not yet approved)
    pagination = (
        Article.query
        .order_by(Article.review_status.asc(), Article.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template('admin/review.html', articles=pagination.items, pagination=pagination)


@admin_bp.route('/review/<int:article_id>/approve', methods=['POST'])
@admin_required
def review_approve(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        flash('文章不存在。', 'error')
        return redirect(url_for('admin.review'))

    gh = get_gh_service()
    approve_article(article, gh, article_base_url=get_base_url())
    flash(f'「{article.title}」审核通过！', 'success')
    return redirect(url_for('admin.review'))


@admin_bp.route('/review/<int:article_id>/reject', methods=['POST'])
@admin_required
def review_reject(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        flash('文章不存在。', 'error')
        return redirect(url_for('admin.review'))

    reject_article(article)
    flash(f'「{article.title}」已拒绝。', 'info')
    return redirect(url_for('admin.review'))


# ---- Article Management (only approved articles) ----
@admin_bp.route('/articles')
@admin_required
def articles():
    page = request.args.get('page', 1, type=int)
    pagination = (
        Article.query
        .filter_by(review_status='approved')
        .order_by(Article.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template('admin/articles.html', articles=pagination.items, pagination=pagination)


@admin_bp.route('/articles/new', methods=['GET', 'POST'])
@admin_required
def article_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        summary = request.form.get('summary', '').strip()
        is_published = request.form.get('is_published') == 'on'

        if not title:
            flash('标题不能为空。', 'error')
            return render_template('admin/article_form.html', article=None)

        create_article(title=title, content=content, tags=tags, summary=summary,
                       is_published=is_published, author_id=current_user.id)
        flash('文章创建成功！发布后需审核通过才会公开可见。', 'success')
        return redirect(url_for('admin.articles'))

    return render_template('admin/article_form.html', article=None)


@admin_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@admin_required
def article_edit(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        flash('文章不存在。', 'error')
        return redirect(url_for('admin.articles'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        summary = request.form.get('summary', '').strip()
        is_published = request.form.get('is_published') == 'on'

        if not title:
            flash('标题不能为空。', 'error')
            return render_template('admin/article_form.html', article=article)

        gh = get_gh_service()
        update_article(
            article=article, title=title, content=content, tags=tags,
            summary=summary, is_published=is_published, gh_service=gh,
            article_base_url=get_base_url(),
        )
        flash('文章更新成功！', 'success')
        return redirect(url_for('admin.articles'))

    return render_template('admin/article_form.html', article=article)


@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@admin_required
def article_delete(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        flash('文章不存在。', 'error')
        return redirect(url_for('admin.articles'))

    gh = get_gh_service()
    delete_article(article, gh)
    flash('文章已删除。', 'info')
    return redirect(url_for('admin.articles'))


# ---- User Management ----
@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    pagination = (
        User.query
        .order_by(User.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template('admin/users.html', users=pagination.items, pagination=pagination)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在。', 'error')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('不能修改自己的管理员权限。', 'error')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    db.session.commit()
    status = '管理员' if user.is_admin else '普通用户'
    flash(f'用户 {user.username} 已被设为 {status}。', 'success')
    return redirect(url_for('admin.users'))
