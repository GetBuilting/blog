import markdown
from flask import Blueprint, render_template, request
from models import Article
from services.article_service import get_all_tags

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = (
        Article.query
        .filter_by(is_published=True, review_status='approved')
        .order_by(Article.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    return render_template('index.html', articles=pagination.items, pagination=pagination)


@blog_bp.route('/archive')
def archive():
    page = request.args.get('page', 1, type=int)
    tag = request.args.get('tag', '').strip()

    query = Article.query.filter_by(is_published=True, review_status='approved')
    if tag:
        query = query.filter(Article.tags.contains(tag))

    pagination = (
        query.order_by(Article.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )

    all_tags = get_all_tags()
    return render_template(
        'archive.html',
        articles=pagination.items,
        pagination=pagination,
        current_tag=tag,
        all_tags=all_tags,
    )


@blog_bp.route('/article/<slug>')
def detail(slug):
    article = Article.query.filter_by(slug=slug, is_published=True, review_status='approved').first_or_404()
    article_html = markdown.markdown(
        article.content,
        extensions=['extra', 'codehilite', 'toc', 'fenced_code'],
    )
    return render_template('detail.html', article=article, article_html=article_html)


@blog_bp.route('/about')
def about():
    return render_template('about.html')
