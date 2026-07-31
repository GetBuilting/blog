# mini_mall 🏠

微型个人博客系统 — 基于 Flask + GitHub Issues + Primer.css。

## 功能

- ✅ 用户注册与登录
- ✅ 文章归档、标签筛选、分页
- ✅ Markdown 写作与代码高亮
- ✅ 基于 GitHub Issues 的评论系统 (utteranc.es)
- ✅ 文章书签收藏
- ✅ 后台管理：文章 CRUD + 用户管理
- ✅ 响应式设计 (Primer.css)

## 技术栈

| 技术 | 版本 |
|------|------|
| Python | 3.12 |
| Flask | 3.1.0 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Login | 0.6.3 |
| PyGithub | 2.6.1 |
| Primer.css | 21.5.1 |
| SQLite | — |

详见 [ARCHITECTURE.md](ARCHITECTURE.md)

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd mini_mall
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 GitHub Token 等配置
```

**必填配置:**
- `SECRET_KEY`: 随机字符串
- `GITHUB_REPO`: 你的 GitHub 仓库 (格式: `username/repo`)
- `GITHUB_TOKEN`: GitHub Personal Access Token (scope: `repo`)

### 5. 运行

```bash
python run.py
```

浏览器访问 `http://localhost:5000`

### 6. 设置管理员

```bash
sqlite3 instance/mini_mall.db "UPDATE users SET is_admin=1 WHERE id=1;"
```

## 项目结构

```
mini_mall/
├── app.py              # Flask 应用入口
├── config.py           # 配置
├── models.py           # 数据模型
├── run.py              # 启动脚本
├── routes/             # 路由 (Blueprint)
├── services/           # 业务逻辑
├── templates/          # Jinja2 模板
├── static/             # 静态资源
└── .github/workflows/  # CI/CD
```

## 部署

项目使用 GitHub Actions 进行 CI/CD，部署脚本在 `.github/workflows/deploy.yml`。需要配置 VPS 的 SSH 密钥作为 GitHub Secrets 实现自动部署。

## License

MIT
