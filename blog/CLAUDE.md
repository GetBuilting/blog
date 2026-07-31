# CLAUDE.md

> Claude 项目上下文文件 — 描述项目架构、技术栈、开发规范与关键约定。

## 项目概述

**blog** 是一个微型个人博客系统，基于 Flask 动态 Web 应用，使用 GitHub Issues 作为评论后端（utteranc.es）。UI 层使用 GitHub Primer.css，支持多用户写作、审核流程、书签收藏、个人相册等功能。

- **类型**: Flask Web 应用（服务端渲染 + SPA 增强）
- **作者**: GetBuilting
- **许可证**: MIT

---

## 常用命令

### 开发

```bash
python -m venv venv && source venv/bin/activate  # 或 venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # 编辑填入 SECRET_KEY / GITHUB_REPO / GITHUB_TOKEN
python run.py                                     # 监听 127.0.0.1:5000
```

### 管理员

```bash
python -c "from app import create_app; create_app()"   # 自动建表
flask admin <username>                                  # 将已注册用户设为管理员
```

### 生产

```bash
waitress-serve --host=0.0.0.0 --port=5000 wsgi:application  # Windows
gunicorn "app:create_app('production')"                       # Linux / Render
```

---

## 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 运行时 | Python | 3.12 | — |
| Web 框架 | Flask | 3.1.0 | 应用工厂模式 `create_app()` |
| ORM | Flask-SQLAlchemy | 3.1.1 | SQLite 数据库操作 |
| 认证 | Flask-Login | 0.6.3 | 会话管理 |
| 密码 | Werkzeug | 3.1.0 | pbkdf2:sha256 |
| GitHub API | PyGithub | 2.6.1 | Issues 评论同步 |
| Markdown | Python-Markdown | 3.7 | extra / codehilite / fenced_code |
| CSS | Primer.css | 21.5.1 | GitHub 风格 UI（CDN） |
| 评论 | utteranc.es | — | GitHub Issues 免费评论 |
| WSGI | Waitress / Gunicorn | 3.0 / 23.0 | 生产服务器 |
| 前端 JS | 原生 JavaScript | — | 无框架，SPA + 事件委托 |

---

## 项目结构

```
blog/
├── app.py                     # Flask 应用工厂 + 蓝图注册 + CLI 命令
├── config.py                  # Config / DevelopmentConfig / ProductionConfig
├── models.py                  # 数据模型: User, Article, Bookmark, Photo
├── run.py                     # 开发启动
├── wsgi.py                    # 生产 WSGI 入口
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
│
├── routes/                    # Blueprint 路由层
│   ├── auth.py                # 登录/注册/个人中心/个人相册
│   ├── blog.py                # 首页/归档/详情/关于
│   ├── bookmarks.py           # 书签增删查
│   ├── admin.py               # 后台仪表盘/审核/文章CRUD/用户管理/图片上传
│   └── my_articles.py         # 用户个人文章CRUD
│
├── services/                  # 业务逻辑层
│   ├── github_service.py      # GitHub Issues API 封装
│   └── article_service.py     # 文章 CRUD + slug + Issue 同步 + 审核
│
├── templates/                 # Jinja2 模板
│   ├── base.html              # 基础布局 + 视频背景 + 确认弹窗 + Toast
│   ├── index.html             # 首页（最新10篇 + 作者显示）
│   ├── archive.html           # 归档 + 青草绿标签筛选 + 分页
│   ├── detail.html            # 文章详情 + utteranc.es 评论区 + 书签按钮
│   ├── about.html             # 关于页
│   ├── bookmarks.html         # 用户书签列表
│   ├── my_articles.html       # 用户文章管理（审核状态列）
│   ├── my_article_form.html   # 用户文章编辑（Markdown + 图片上传 + 标签下拉）
│   ├── auth/                  # login / register / profile / album
│   └── admin/                 # dashboard / review / articles / article_form / users
│
├── static/
│   ├── css/style.css          # 全局样式 + Toast + 确认弹窗 + 编辑器 + 灯箱
│   ├── js/main.js             # SPA 导航 + Toast + 确认弹窗 + 书签事件委托 + 图片上传
│   ├── videos/beauty.mp4      # 背景视频
│   └── uploads/               # 用户上传图片（photos/ 子目录）
│
└── .github/workflows/deploy.yml
```

---

## 数据模型

### User (`users`)
| 字段 | 说明 |
|------|------|
| id, username (UNIQUE), email (UNIQUE) | 基本标识 |
| nickname | 显示昵称（`display_name` 属性优先返回昵称） |
| avatar | emoji 头像 |
| password_hash | Werkzeug pbkdf2:sha256 |
| is_admin | 管理员标记（首用户需手动设） |
| → bookmarks | one-to-many → Bookmark |
| → articles | one-to-many → Article（作者） |
| → photos | one-to-many → Photo |

### Article (`articles`)
| 字段 | 说明 |
|------|------|
| id, title, slug (UNIQUE), content | 基本内容 |
| summary | 摘要（空时自动取正文前200字） |
| tags | 逗号分隔标签，`tag_list` 属性返回列表 |
| is_published | 发布开关 |
| review_status | `pending` / `approved` / `rejected` |
| author_id | FK → users（可为空兼容旧数据） |
| github_issue_number | utteranc.es 评论 Issue 号 |
| created_at / updated_at | UTC 时间 |
| → bookmarks | one-to-many → Bookmark |

### Bookmark (`bookmarks`)
- `id`, `user_id` (FK), `article_id` (FK)
- UNIQUE(user_id, article_id) — 防重复收藏

### Photo (`photos`)
- `id`, `user_id` (FK), `filename`, `original_name`, `created_at`
- 文件存 `static/uploads/photos/`，每人最多 10 张

---

## 关键架构决策

### 1. 文章审核流程

```
创建文章 → pending（管理员自动 approved）
普通用户创建 → pending → 管理员审核 → approved / rejected
编辑文章 → 自动重置为 pending（需重新审核）
驳回已通过文章 → 操作栏"驳回审核"按钮
```

公开路由只查 `is_published=True AND review_status='approved'`。

### 2. SPA 导航与 JS 架构

`main.js` 拦截 `<a>` 点击 → `fetch()` → `DOMParser` → 替换 `.site-main` 内容。注意：
- `.site-main` **外部**的 `<script>`（如 `extra_scripts`）**不会**重新执行
- `.site-main` **内部**的 `<script>` 会被 SPA 重新执行
- 书签、确认弹窗等用**事件委托**挂在 `document` 上，SPA 后仍然有效
- 编辑器的 Markdown 预览脚本必须放在 `content` 块内部

### 3. Markdown 编辑器

两个编辑页面（后台 `admin/article_form.html` + 用户 `my_article_form.html`）：
- 左右分屏：Markdown 源码 + 实时预览
- 图片上传按钮 → `/admin/upload-image` → 自动插入 `![](url)`
- 标签下拉框：代码/生活/游戏/娱乐/书籍分享/其他（选"其他"可手写）
- marked.js 动态加载（`ensureMarked()` 函数）

### 4. 全局弹窗系统

- **Toast 通知**：`showToast(message, type)` — 居中淡入，2 秒自动消失
- **确认弹窗**：`showConfirm(message, icon, okText, okClass, callback)` — 青草绿高亮，ESC/背景关闭
- 表单用 `class="confirm-form" data-confirm="..."` 属性，main.js 事件委托拦截

### 5. 视频背景

`base.html` 中 `<video>` fixed 背景 + 半透明白色遮罩，`.site-main` 半透明背景确保可读。

### 6. 用户菜单

纯 CSS hover 下拉菜单，无形桥接区防消失。显示用户 avatar + display_name。

---

## 编码规范

### Python
- 路由放 `routes/`，业务逻辑放 `services/`
- 时间统一 `datetime.now(timezone.utc)`（UTC）
- GitHub API 异常捕获 `GithubException`
- 上传文件验证扩展名白名单 + UUID 重命名

### 模板
- 全部继承 `base.html`
- Primer.css CDN + 自定义 `style.css`
- Flash: `success` → `flash-success`, `error` → `flash-error`, `info` → `flash-warn`
- 确认弹窗表单：`class="confirm-form"` + `data-confirm` / `data-icon` / `data-ok` 属性

### JavaScript
- 原生 JS，无框架依赖
- SPA 外部交互（书签、弹窗、退出登录）用**事件委托**在 `document` 监听
- JS 版本号 `?v=N` 防缓存

### 数据库
- SQLite `instance/blog.db`（gitignored）
- `db.create_all()` 自动建表，无迁移工具
- 新增字段时需删除旧数据库重建

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 生产必填 | Flask session 密钥 |
| `GITHUB_REPO` | 评论必填 | 格式 `username/repo` |
| `GITHUB_TOKEN` | 评论必填 | PAT，需 `repo` scope |
| `DATABASE_URL` | 可选 | 默认 `sqlite:///blog.db` |
| `BASE_URL` | 生产推荐 | 站点完整 URL |

---

## 注意事项

1. **首个注册用户不是管理员** — 需 `flask admin <username>`
2. **公开查询双条件** — `is_published=True AND review_status='approved'`
3. **编辑后重新审核** — 更新文章自动重置为 pending
4. **SPA 脚本位置** — 需 SPA 重新执行的脚本放 `content` 块内，不要放 `extra_scripts`
5. **slug 中文兜底** — 纯中文标题生成 `post-xxxxxxxx` 格式 slug
6. **相册限额** — 每人最多 10 张，前端+后端双重校验
7. **GitHub 未配置** — 优雅降级，文章正常管理但无评论区
8. **部署** — Render 自动部署，Root Directory 设为 `blog`
