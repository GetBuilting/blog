"""用户个人文章管理 — CRUD for user's own articles."""
import re
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Article

my_articles_bp = Blueprint('my_articles', __name__, url_prefix='/my')


def _generate_slug(title: str, existing_id: int | None = None) -> str:
    """Generate a URL-friendly slug from title."""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug.strip('-')
    base_slug = slug
    counter = 1
    while True:
        q = Article.query.filter_by(slug=slug)
        if existing_id:
            q = q.filter(Article.id != existing_id)
        if not q.first():
            break
        slug = f'{base_slug}-{counter}'
        counter += 1
    return slug


@my_articles_bp.route('/articles')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = (
        current_user.articles
        .order_by(Article.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    return render_template('my_articles.html', articles=pagination.items, pagination=pagination)


@my_articles_bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        summary = request.form.get('summary', '').strip()

        if not title:
            flash('标题不能为空。', 'error')
            return render_template('my_article_form.html')

        slug = _generate_slug(title)
        article = Article(
            title=title,
            slug=slug,
            content=content,
            summary=summary or content[:200],
            tags=tags,
            is_published=True,
            review_status='pending',
            author_id=current_user.id,
        )
        db.session.add(article)
        db.session.commit()
        flash('文章发布成功！', 'success')
        return redirect(url_for('my_articles.index'))

    return render_template('my_article_form.html')


@my_articles_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(article_id):
    article = db.session.get(Article, article_id)
    if not article or article.author_id != current_user.id:
        flash('文章不存在或无权编辑。', 'error')
        return redirect(url_for('my_articles.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        summary = request.form.get('summary', '').strip()

        if not title:
            flash('标题不能为空。', 'error')
            return render_template('my_article_form.html', article=article)

        article.title = title
        article.slug = _generate_slug(title, existing_id=article.id)
        article.content = content
        article.summary = summary or content[:200]
        article.tags = tags
        article.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('文章更新成功！', 'success')
        return redirect(url_for('my_articles.index'))

    return render_template('my_article_form.html', article=article)


@my_articles_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete(article_id):
    article = db.session.get(Article, article_id)
    if not article or article.author_id != current_user.id:
        flash('文章不存在或无权删除。', 'error')
        return redirect(url_for('my_articles.index'))

    db.session.delete(article)
    db.session.commit()
    flash('文章已删除。', 'info')
    return redirect(url_for('my_articles.index'))
