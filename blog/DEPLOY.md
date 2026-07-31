# Render 部署指南（推荐）

Render 完全免费，从 GitHub 自动部署，无需手动配置服务器。

## 第 1 步：注册 Render

打开 [render.com](https://render.com) → 用 GitHub 账号登录

## 第 2 步：创建 Web Service

1. 点击 **New** → **Web Service**
2. 选择你的 GitHub 仓库 `GetBuilting/blog`
3. 填写配置：

| 配置项 | 值 |
|--------|-----|
| **Name** | mini-mall（随便取） |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn "app:create_app('production')"` |

4. 点击 **Advanced** → 添加环境变量：

| Key | Value |
|-----|-------|
| `SECRET_KEY` | 随机字符串（键盘乱敲） |
| `GITHUB_REPO` | `GetBuilting/blog` |
| `GITHUB_TOKEN` | `ghp_你的Token` |
| `PYTHON_VERSION` | `3.12.0` |

5. 选择 **Free** 计划
6. 点击 **Create Web Service**

## 第 3 步：等待部署

Render 自动 clone 代码 → 装依赖 → 启动服务，约 2-3 分钟。完成后访问：

`https://mini-mall.onrender.com`

## 更新代码

每次 `git push` 到 GitHub，Render 自动重新部署，无需手动操作。

---

# PythonAnywhere 部署指南（备选）

<details>
<summary>展开查看</summary>

## 第 1 步：打开 Bash 终端

点击 PythonAnywhere 顶部的 **Consoles** → **Bash**

## 第 2 步：克隆代码

```bash
git clone https://github.com/GetBuilting/blog.git
cd blog
```

## 第 3 步：创建虚拟环境并安装依赖

```bash
mkvirtualenv --python=/usr/bin/python3.12 mini_mall
pip install -r requirements.txt
```

## 第 4 步：配置 .env

```bash
nano .env
```

```ini
SECRET_KEY=乱敲一串字符
GITHUB_REPO=GetBuilting/blog
GITHUB_TOKEN=ghp_你的Token
BASE_URL=https://你的用户名.pythonanywhere.com
```

## 第 5 步：初始化数据库

```bash
python -c "from app import create_app; create_app()"
```

## 第 6 步：配置 Web App

1. Web → Add a new web app → Manual configuration → Python 3.12
2. 编辑 WSGI configuration file：

```python
import sys
import os

project_home = '/home/你的用户名/blog'
os.chdir(project_home)
sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from app import create_app
application = create_app('production')
```

3. Virtualenv: `/home/你的用户名/.virtualenvs/mini_mall`
4. 点击 Reload

</details>
