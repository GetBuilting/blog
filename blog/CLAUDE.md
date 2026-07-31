# CLAUDE.md

> Claude 项目上下文文件 — 描述项目架构、技术栈、开发规范与关键约定。

## 项目概述

**blog**（原名 mini_mall）是一个微型个人博客系统，基于 Flask 动态 Web 应用，使用 GitHub Issues 作为评论后端（utteranc.es）。UI 层使用 GitHub Primer.css 实现响应式设计。

- **类型**: Flask Web 应用（服务端渲染）
- **作者**: GetBuilting
- **许可证**: MIT

---

## 常用命令

### 开发

```bash
# 创建虚拟环境 & 安装依赖
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 配置环境变量（需要 GitHub Token）
cp .env.example .env
# 编辑 .env 填入 SECRET_KEY / GITHUB_REPO / GITHUB_TOKEN

# 启动开发服务器
python run.py              # 监听 127.0.0.1:5000

# 初始化数据库 & 设置管理员
python -c "from app import create_app; create_app()"   # 自动建表
flask admin <username>                                  # 将已注册用户设为管理员
```

### 生产

```bash
# Waitress (Windows / 轻量部署)
waitress-serve --host=0.0.0.0 --port=5000 wsgi:application

# Gunicorn (Linux / Render)
gunicorn "app:create_app('production')"
```

### 项目中没有自动化测试（`deploy.yml` 里只有 echo 占位）。

---

## 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 运行时 | Python | 3.12 | — |
| Web 框架 | Flask | 3.1.0 | 应用工厂模式 `create_app()` |
| ORM | Flask-SQLAlchemy | 3.1.1 | 数据库操作 |
| 数据库 | SQLite | stdlib | 文件型数据库 `instance/blog.db` |
| 认证 | Flask-Login | 0.6.3 | 会话管理 + `@login_required` |
| 密码哈希 | Werkzeug | 3.1.0 | `generate_password_hash` / `check_password_hash` |
| 表单 | Flask-WTF | 1.2.2 | CSRF 保护（已引入但表单验证用手写） |
| GitHub API | PyGithub | 2.6.1 | 为每篇通过审核的文章创建 GitHub Issue |
| Markdown | Python-Markdown | 3.7 | 文章渲染（extra / codehilite / toc / fenced_code） |
| CSS | Primer.css | 21.5.1 | GitHub 风格 UI（CDN 引入） |
| 评论 | utteranc.es | — | 基于 GitHub Issues 的免费评论 |
| WSGI | Waitress | 3.0.0 | Windows 生产服务器 |
| WSGI | Gunicorn | 23.0.0 | Linux 生产服务器 |
| 环境变量 | python-dotenv | 1.0.1 | `.env` 加载 |

---

## 项目结构

```
blog/
├── app.py                     # Flask 应用工厂入口 → create_app()
├── config.py                  # Config / DevelopmentConfig / ProductionConfig
├── models.py                  # SQLAlchemy 模型: User, Article, Bookmark
├── run.py                     # 开发启动脚本
├── wsgi.py                    # 生产 WSGI 入口 (PythonAnywhere / Waitress)
├── requirements.txt
├── .env.example               # 环境变量模板
│
├── routes/                    # Blueprint 路由层
│   ├── auth.py                # /register, /login, /logout
│   ├── blog.py                # /, /archive, /article/<slug>, /about
│   ├── bookmarks.py           # /bookmarks/, /bookmarks/toggle/<id>
│   └── admin.py               # /admin/* (dashboard, review, articles CRUD, users)
│
├── services/                  # 业务逻辑层
│   ├── github_service.py      # GitHub Issues API 封装 (create/update/close)
│   └── article_service.py     # 文章 CRUD + slug 生成 + Issue 同步 + 审核流程
│
├── templates/                 # Jinja2 模板
│   ├── base.html              # 基础布局 (Header + Footer + 视频背景)
│   ├── index.html             # 首页 (最新10篇)
│   ├── archive.html           # 归档 + 标签筛选 + 分页
│   ├── detail.html            # 文章详情 + utteranc.es 评论区 + 书签按钮
│   ├── about.html             # 关于页
│   ├── bookmarks.html         # 用户书签列表
│   ├── auth/login.html / register.html
│   └── admin/                 # dashboard / review / articles / article_form / users
│
├── static/
│   ├── css/style.css          # 自定义样式 (动画/编辑器/管理面板/响应式)
│   ├── js/main.js             # SPA-like 页面切换 + 书签交互
│   └── videos/beauty.mp4      # 背景视频
│
└── .github/workflows/
    └── deploy.yml             # CI/CD (占位，未配置真实部署)
```

---

## 数据模型

### User (`users`)
- `id` (PK), `username` (UNIQUE, INDEX), `email` (UNIQUE)
- `password_hash` — Werkzeug pbkdf2:sha256
- `is_admin` (default False) — 首个注册用户需手动设为管理员
- `bookmarks` — one-to-many → Bookmark (cascade delete)

### Article (`articles`)
- `id` (PK), `title`, `slug` (UNIQUE, INDEX), `content` (Markdown), `summary`, `tags` (逗号分隔)
- `is_published` (Boolean) — 文章发布开关
- `review_status` — `'pending'` | `'approved'` | `'rejected'` (默认 pending)
- `github_issue_number` (nullable) — 审核通过后创建 Issue，用于 utteranc.es
- `created_at` / `updated_at` — UTC 时间
- `tag_list` — @property，返回拆分后的标签列表

### Bookmark (`bookmarks`)
- `id` (PK), `user_id` (FK), `article_id` (FK)
- UNIQUE(`user_id`, `article_id`) — 防重复收藏

---

## 关键架构决策

### 1. 文章审核流程（review_status）

```
创建文章 → review_status = 'pending'（is_published 可以为 True，但前端不可见）
         → 管理员审核通过 → review_status = 'approved' + 自动创建 GitHub Issue
         → 管理员拒绝 → review_status = 'rejected'
```

**重要**: 公开路由（`blog.py`）只查询 `is_published=True AND review_status='approved'` 的文章。审核通过后才创建 GitHub Issue 和 utteranc.es 评论区。

### 2. GitHub Issues 同步机制

- **创建 Issue**: 仅发生在 `approve_article()` 时，调用 `github_service.create_issue()`
- **更新 Issue**: `update_article()` 仅在 `review_status == 'approved'` 且已有 `github_issue_number` 时更新
- **关闭 Issue**: 取消发布 (`is_published=False`) 或删除文章时调用 `close_issue()`
- **未配置 GitHub 时优雅降级**: `is_configured()` 检查 `token` 和 `repo_name` 均非空

### 3. SPA-like 页面切换

`static/js/main.js` 拦截所有站内链接的点击事件，通过 `fetch()` 获取目标页面 HTML，用 `DOMParser` 提取 `.site-main` 内容替换，配合 CSS `opacity` + `transform` 实现淡入淡出动画。浏览器前进/后退通过 `popstate` 事件支持。失败时回退到完整页面导航。

### 4. 视频背景

`base.html` 包含一个固定在背后的 `<video>` 标签（`position: fixed; z-index: -2`）和半透明白色遮罩层（`z-index: -1`）。内容区 `.site-main` 使用 `rgba(255,255,255,0.6)` 半透明背景确保可读性。视频路径: `static/videos/beauty.mp4`。

### 5. 应用工厂模式

`app.py` 使用 `create_app(config_name)` 工厂函数，支持 `'development'` / `'production'` / `'default'` 三种配置。所有 Blueprint 和 CLI 命令在工厂内注册，便于测试和不同环境部署。

### 6. 自定义用户菜单

导航栏用户头像下拉菜单使用纯 CSS hover 实现（`.user-menu:hover .user-menu-dropdown`），无需 JS。菜单与触发按钮之间有无形桥接区域防止鼠标移动时菜单消失。

---

## 编码规范 & 约定

### Python
- **路由**: 每个 Blueprint 一个文件，放在 `routes/` 下
- **业务逻辑**: 放在 `services/` 下，不在路由中直接写复杂逻辑
- **模型**: 所有 ORM 模型集中在 `models.py`，使用 `db = SQLAlchemy()` 全局实例
- **时间处理**: 统一使用 `datetime.now(timezone.utc)`（UTC），不使用 naive datetime
- **日志**: 使用标准 `logging.getLogger(__name__)`
- **错误处理**: GitHub API 调用捕获 `GithubException`，返回 `None` 或 `False`

### 模板
- **继承链**: 所有页面 → `base.html`
- **CSS 框架**: Primer.css 通过 CDN 引入（`@primer/css@21.5.1`），自定义样式在 `static/css/style.css`
- **标签样式**: 使用 Primer 的 `Label Label--secondary` 组件
- **Flash 消息**: 类别映射 — `success` → `flash-success`, `error` → `flash-error`, `info` → `flash-warn`

### JavaScript
- **无框架**: 原生 JS，不依赖任何 JS 库
- **书签功能**: `toggleBookmark(btn)` 全局函数，在 `detail.html` 的 `extra_scripts` 块中重复定义（`main.js` 中也有，因为 SPA 切换会重新加载内联脚本）
- **SPA 导航**: 拦截 `<a>` 点击（排除外部链接 / `#` / `javascript:` / `target=_blank` / `download` / form 内链接）

### 数据库
- SQLite 文件位于 `instance/blog.db`（已在 `.gitignore` 中排除）
- 首次运行时 `db.create_all()` 自动建表，无迁移工具

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 生产必填 | Flask session 加密密钥 |
| `GITHUB_REPO` | 评论功能必填 | 格式 `username/repo`（如 `GetBuilting/blog`） |
| `GITHUB_TOKEN` | 评论功能必填 | GitHub PAT，需要 `repo` scope |
| `DATABASE_URL` | 可选 | 默认 `sqlite:///blog.db` |
| `BASE_URL` | 生产推荐 | 站点完整 URL，用于生成 Issue 中的回链 |
| `FLASK_ENV` | 可选 | `development` / `production` |

---

## 注意事项 & 常见陷阱

1. **首个注册用户不是管理员** — 必须通过 `flask admin <username>` 或直接操作 SQLite 手动设置 `is_admin=1`
2. **文章公开可见的双重条件** — 所有公开查询必须同时满足 `is_published=True` AND `review_status='approved'`。只查 `is_published` 会导致待审核文章泄露。
3. **GitHub Token 未配置时** — 文章仍可正常创建和管理，只是不会创建 Issue，评论区会显示"评论功能暂未开启"
4. **slug 唯一性** — `_generate_slug()` 自动处理重名，追加 `-1`, `-2` 等后缀
5. **SPA 切换可能丢状态** — 内联 `<script>` 块在 SPA 切换后会通过 `replaceChild` + `newScript` 重新执行，但如果需要清理旧的事件监听器，需额外处理
6. **背景视频文件较大** — `static/videos/beauty.mp4` 已在 `.gitignore` 中通过 `static/videos/` 排除，部署时需手动上传
7. **部署** — 首选 Render（自动从 GitHub 部署），备选 PythonAnywhere。`deploy.yml` 目前只有占位 echo，未配置真实 SSH 部署。

---

## 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) — 详细架构设计文档
- [DEPLOY.md](DEPLOY.md) — Render / PythonAnywhere 部署指南
- [README.md](README.md) — 项目简介与快速开始
