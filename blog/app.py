from flask import Flask
from flask_login import LoginManager
from config import config
from models import db, User


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录后再访问此页面。'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app(config_name=None):
    if config_name is None:
        config_name = 'default'

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.blog import blog_bp
    from routes.bookmarks import bookmarks_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(bookmarks_bp)
    app.register_blueprint(admin_bp)

    # Register context processors
    from flask import g

    @app.context_processor
    def inject_site_config():
        return {
            'site_name': app.config.get('SITE_NAME', 'blog'),
            'site_description': app.config.get('SITE_DESCRIPTION', ''),
        }

    # Create tables
    with app.app_context():
        db.create_all()

    # CLI command: flask admin <username>
    import click as _click
    @app.cli.command('admin')
    @_click.argument('username')
    def set_admin(username):
        """Set a user as admin. Usage: flask admin <username>"""
        user = User.query.filter_by(username=username).first()
        if not user:
            _click.echo(f'User "{username}" not found. Register first.')
            return
        user.is_admin = True
        db.session.commit()
        _click.echo(f'User "{username}" is now admin.')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
