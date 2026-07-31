from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models import db, Article, Bookmark

bookmarks_bp = Blueprint('bookmarks', __name__)


@bookmarks_bp.route('/')
@login_required
def my_bookmarks():
    page = request.args.get('page', 1, type=int)
    pagination = (
        current_user.bookmarks
        .order_by(Bookmark.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    articles = [bm.article for bm in pagination.items]
    return render_template('bookmarks.html', articles=articles, pagination=pagination)


@bookmarks_bp.route('/toggle/<int:article_id>', methods=['POST'])
@login_required
def toggle(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        return jsonify({'status': 'error', 'message': '文章不存在'}), 404

    existing = Bookmark.query.filter_by(
        user_id=current_user.id, article_id=article_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'status': 'removed', 'message': '已取消收藏'})
    else:
        bookmark = Bookmark(user_id=current_user.id, article_id=article_id)
        db.session.add(bookmark)
        db.session.commit()
        return jsonify({'status': 'added', 'message': '已收藏'})
