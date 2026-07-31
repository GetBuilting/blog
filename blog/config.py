import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///blog.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # GitHub config for utteranc.es comments & Issue management
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    GITHUB_REPO = os.getenv('GITHUB_REPO', '')  # format: 'username/repo'

    # Site config
    SITE_NAME = '个人博客网'
    SITE_DESCRIPTION = '一个自由小型博客'
    POSTS_PER_PAGE = 10


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
