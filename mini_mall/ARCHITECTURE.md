# mini_mall 架构设计文档

## 项目概述

**mini_mall** 是一个微型个人博客系统，基于 Flask 动态 Web 应用架构，使用 GitHub Issues 作为评论后端。

## 技术栈 (精确版本)

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **运行时** | Python | 3.12 | — |
| **Web 框架** | Flask | 3.1.0 | 应用核心 |
| **ORM** | Flask-SQLAlchemy | 3.1.1 | 数据库操作 |
| **数据库** | SQLite | stdlib | 用户、文章、书签 |
| **认证** | Flask-Login | 0.6.3 | 会话管理 |
| **密码哈希** | Werkzeug | 3.1.0 | generate_password_hash |
| **表单** | Flask-WTF | 1.2.2 | CSRF + 表单验证(预留) |
| **模板** | Jinja2 | 3.1.0 | Flask 内置 |
| **GitHub API** | PyGithub | 2.6.1 | 为每篇文章创建 Issue(评论用) |
| **Markdown** | Python-Markdown | 3.7 | 文章渲染 |
| **CSS** | Primer.css | 21.5.1 | GitHub 风格 UI |
| **评论** | utteranc.es | — | 基于 GitHub Issues |
| **CI/CD** | GitHub Actions | — | 自动化部署 |
| **WSGI** | Waitress | 3.0.0 | 生产环境服务器 |

---

## 目录结构

```
mini_mall/
├── app.py                     # Flask 应用工厂入口
├── config.py                  # 配置类 (Dev/Prod)
├── models.py                  # SQLAlchemy 数据模型
├── run.py                     # 开发启动脚本
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── .gitignore
├── ARCHITECTURE.md            # 本架构文档
│
├── routes/                    # Blueprint 路由层
│   ├── __init__.py
│   ├── auth.py                # 登录/注册/登出
│   ├── blog.py                # 首页/归档/详情/关于
│   ├── bookmarks.py           # 书签增删查
│   └── admin.py               # 后台 CRUD + 用户管理
│
├── services/                  # 业务逻辑层
│   ├── __init__.py
│   ├── github_service.py      # GitHub Issues API 封装
│   └── article_service.py     # 文章 CRUD + Issue 同步
│
├── templates/                 # Jinja2 模板
│   ├── base.html              # 基础布局 (Primer.css Header + Footer)
│   ├── index.html             # 首页
│   ├── archive.html           # 归档 + 标签筛选
│   ├── detail.html            # 文章详情 + utteranc.es + 书签
│   ├── about.html             # 关于页
│   ├── bookmarks.html         # 用户书签
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── admin/
│       ├── dashboard.html     # 仪表盘
│       ├── articles.html      # 文章列表管理
│       ├── article_form.html  # 新建/编辑表单
│       └── users.html         # 用户管理
│
├── static/
│   ├── css/
│   │   └── style.css          # 自定义样式
│   └── js/
│       └── main.js            # 书签交互
│
└── .github/workflows/
    └── deploy.yml             # CI/CD 部署
```

---

## 数据模型

### User (users)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| username | String(64) | UNIQUE, NOT NULL, INDEX | 登录名 |
| email | String(128) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | String(256) | NOT NULL | Werkzeug 哈希 |
| is_admin | Boolean | DEFAULT False | 管理员标记 |
| created_at | DateTime | DEFAULT utcnow | 注册时间 |

关联: `bookmarks` → Bookmark (one-to-many, cascade delete)

### Article (articles)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| title | String(256) | NOT NULL | 标题 |
| slug | String(256) | UNIQUE, NOT NULL, INDEX | URL 友好标识 |
| content | Text | NOT NULL | Markdown 正文 |
| summary | String(512) | — | 摘要(列表显示) |
| tags | String(256) | — | 逗号分隔标签 |
| is_published | Boolean | DEFAULT False | 发布状态 |
| github_issue_number | Integer | NULLABLE | utteranc.es 评论 Issue 号 |
| created_at | DateTime | DEFAULT utcnow | 创建时间 |
| updated_at | DateTime | ON UPDATE utcnow | 更新时间 |

关联: `bookmarks` → Bookmark (one-to-many, cascade delete)

### Bookmark (bookmarks)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| user_id | Integer | FK → users.id | 用户 |
| article_id | Integer | FK → articles.id | 文章 |
| created_at | DateTime | DEFAULT utcnow | 收藏时间 |
| — | — | UNIQUE(user_id, article_id) | 去重 |

---

## 路由设计

### 公开路由 (blog)
| 方法 | 路径 | 处理函数 | 功能 |
|------|------|----------|------|
| GET | `/` | `blog.index` | 首页，最新 10 篇文章 |
| GET | `/archive` | `blog.archive` | 归档列表，`?page=` 分页，`?tag=` 筛选 |
| GET | `/article/<slug>` | `blog.detail` | 文章详情 + utteranc.es 评论区 + 书签按钮 |
| GET | `/about` | `blog.about` | 关于页面 |

### 认证路由 (auth)
| 方法 | 路径 | 处理函数 | 功能 |
|------|------|----------|------|
| GET/POST | `/login` | `auth.login` | 登录表单 |
| GET/POST | `/register` | `auth.register` | 注册表单 |
| GET | `/logout` | `auth.logout` | 登出 → 重定向首页 |

### 书签路由 (bookmarks) — 需登录
| 方法 | 路径 | 处理函数 | 功能 |
|------|------|----------|------|
| GET | `/bookmarks/` | `bookmarks.my_bookmarks` | 当前用户书签列表 |
| POST | `/bookmarks/toggle/<id>` | `bookmarks.toggle` | 切换书签 → JSON 响应 |

### 后台路由 (admin) — 需管理员
| 方法 | 路径 | 处理函数 | 功能 |
|------|------|----------|------|
| GET | `/admin/` | `admin.dashboard` | 仪表盘(统计) |
| GET | `/admin/articles` | `admin.articles` | 文章管理列表 |
| GET/POST | `/admin/articles/new` | `admin.article_new` | 新建文章 |
| GET/POST | `/admin/articles/<id>/edit` | `admin.article_edit` | 编辑文章 |
| POST | `/admin/articles/<id>/delete` | `admin.article_delete` | 删除文章 |
| GET | `/admin/users` | `admin.users` | 用户列表 |
| POST | `/admin/users/<id>/toggle-admin` | `admin.toggle_admin` | 切换管理员权限 |

---

## 核心业务流程

### 文章发布流程
```
管理员 POST /admin/articles/new
  → article_service.create_article()
    → 生成 slug（确保唯一）
    → 插入 Article 到 SQLite
    → 如果 is_published:
        → github_service.create_issue(title, body)
        → 将 issue.number 存入 article.github_issue_number
  → 重定向到文章管理列表
```

### 文章编辑流程
```
管理员 POST /admin/articles/<id>/edit
  → article_service.update_article()
    → 更新 Article 字段
    → 如果是发布状态:
        → 有现有 Issue → github_service.update_issue()
        → 无现有 Issue → github_service.create_issue()
    → 如果取消发布:
        → github_service.close_issue()
```

### utteranc.es 评论机制
```
文章详情页 <script> 加载 utteranc.es
  → 指向 GITHUB_REPO 仓库
  → 使用 article.github_issue_number 作为标识
  → 读者在文章下评论 → utteranc.es 写入对应 Issue 的 comment
  → 完全免费，评论数据存储在 GitHub Issues 中
```

### 书签切换流程
```
用户点击收藏/取消按钮
  → POST /bookmarks/toggle/<article_id>
  → 查询 Bookmark 表
  → 存在 → 删除 (取消收藏)
  → 不存在 → 插入 (添加收藏)
  → 返回 JSON: {status: "added"|"removed", message: "..."}
```

---

## 部署架构

```
┌────────────────────────────────────────┐
│            GitHub Actions              │
│  push → pip install → deploy script   │
└──────────────────┬─────────────────────┘
                   │ rsync / scp / ssh
                   ▼
┌────────────────────────────────────────┐
│         VPS / Cloud Server             │
│  ┌─────────────────────────────────┐  │
│  │  Waitress WSGI (port 5000)      │  │
│  │  ┌───────────────────────────┐  │  │
│  │  │  Flask App                │  │  │
│  │  │  ├─ SQLite (mini_mall.db) │  │  │
│  │  │  └─ PyGithub → GitHub API │  │  │
│  │  └───────────────────────────┘  │  │
│  └─────────────────────────────────┘  │
│                   ↕                    │
│     Nginx reverse proxy (port 80/443) │
└────────────────────────────────────────┘
                   ↕
┌────────────────────────────────────────┐
│            GitHub Issues               │
│  utteranc.es comments storage          │
└────────────────────────────────────────┘
```

---

## 安全设计

1. **密码哈希**: Werkzeug `generate_password_hash` (pbkdf2:sha256)
2. **CSRF**: 预留 Flask-WTF CSRF 保护
3. **登录保护**: Flask-Login session + `@login_required` 装饰器
4. **管理员保护**: `@admin_required` 装饰器 + `current_user.is_admin` 检查
5. **GitHub Token**: 通过环境变量注入，不写死在代码中
6. **SECRET_KEY**: 生产环境必须使用随机字符串

## 初始化管理员

首个注册用户默认 `is_admin=False`。设为管理员的方式：

```bash
# 方式1: 直接操作 SQLite
sqlite3 instance/mini_mall.db "UPDATE users SET is_admin=1 WHERE id=1;"

# 方式2: Flask shell
flask shell
>>> from models import db, User
>>> user = User.query.first()
>>> user.is_admin = True
>>> db.session.commit()
```
