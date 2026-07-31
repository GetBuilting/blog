"""
Article service — business logic for creating/updating/deleting articles
and syncing with GitHub Issues for utteranc.es comments.
"""

import re
import logging
from datetime import datetime, timezone

from models import db, Article
from services.github_service import GitHubService

logger = logging.getLogger(__name__)


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


def create_article(title: str, content: str, tags: str, summary: str,
                   is_published: bool, author_id: int = None, **kwargs) -> Article:
    """Create an article. Starts with review_status='pending'."""
    slug = _generate_slug(title)
    article = Article(
        title=title,
        slug=slug,
        content=content,
        summary=summary or content[:200],
        tags=tags,
        is_published=is_published,
        review_status='pending',
        author_id=author_id,
    )
    db.session.add(article)
    db.session.commit()
    return article


def update_article(article: Article, title: str, content: str, tags: str,
                   summary: str, is_published: bool,
                   gh_service: GitHubService,
                   article_base_url: str = '') -> Article:
    """Update an article. Syncs GitHub Issue only if already approved."""
    article.title = title
    article.slug = _generate_slug(title, existing_id=article.id)
    article.content = content
    article.summary = summary or content[:200]
    article.tags = tags
    article.is_published = is_published
    article.updated_at = datetime.now(timezone.utc)

    if article.review_status == 'approved' and article.github_issue_number and gh_service.is_configured():
        article_url = f'{article_base_url}/article/{article.slug}'
        issue_body = gh_service.build_issue_body(article_url, article.summary)
        gh_service.update_issue(article.github_issue_number, f'[Blog] {title}', issue_body)

    if not is_published and article.github_issue_number and gh_service.is_configured():
        gh_service.close_issue(article.github_issue_number)

    db.session.commit()
    return article


def approve_article(article: Article, gh_service: GitHubService,
                    article_base_url: str = '') -> Article:
    """Approve an article — auto-publishes it, creates GitHub Issue and makes it visible."""
    article.is_published = True
    article.review_status = 'approved'
    article.updated_at = datetime.now(timezone.utc)

    if gh_service.is_configured():
        article_url = f'{article_base_url}/article/{article.slug}'
        issue_body = gh_service.build_issue_body(article_url, article.summary)
        issue_number = gh_service.create_issue(
            title=f'[Blog] {article.title}',
            body=issue_body,
            labels=['blog-post', 'comments'],
        )
        article.github_issue_number = issue_number

    db.session.commit()
    return article


def reject_article(article: Article) -> Article:
    """Reject a published article."""
    article.review_status = 'rejected'
    article.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return article


def delete_article(article: Article, gh_service: GitHubService) -> None:
    """Delete an article and close its GitHub Issue."""
    if article.github_issue_number and gh_service.is_configured():
        gh_service.close_issue(article.github_issue_number)

    db.session.delete(article)
    db.session.commit()


def get_all_tags() -> list[str]:
    """Get all unique tags from published + approved articles."""
    articles = Article.query.filter_by(is_published=True, review_status='approved').all()
    tags = set()
    for a in articles:
        for t in a.tag_list:
            tags.add(t)
    return sorted(tags)
