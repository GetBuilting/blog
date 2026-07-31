from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic',
                                cascade='all, delete-orphan')
    articles = db.relationship('Article', backref='author', lazy='dynamic',
                               foreign_keys='Article.author_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_bookmarked(self, article_id):
        return self.bookmarks.filter_by(article_id=article_id).first() is not None

    def __repr__(self):
        return f'<User {self.username}>'


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(256), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False, default='')
    summary = db.Column(db.String(512), default='')
    tags = db.Column(db.String(256), default='')  # comma-separated
    is_published = db.Column(db.Boolean, default=False)
    review_status = db.Column(db.String(16), default='pending')  # pending / approved / rejected
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    github_issue_number = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    bookmarks = db.relationship('Bookmark', backref='article', lazy='dynamic',
                                cascade='all, delete-orphan')

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def __repr__(self):
        return f'<Article {self.title}>'


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='uq_user_article'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Bookmark user={self.user_id} article={self.article_id}>'
