# Render 部署指南

> **缺点**：免费版没有持久磁盘，SQLite 数据可能丢失。推荐 PythonAnywhere。

Render 自动从 GitHub 部署，无需手动配置服务器。

## 第 1 步：注册 Render

打开 [render.com](https://render.com) → 用 GitHub 账号登录

## 第 2 步：创建 Web Service

1. 点击 **New** → **Web Service**
2. 选择仓库 `GetBuilting/blog`
3. 填写配置：

| 配置项 | 值 |
|--------|-----|
| **Name** | blog（随便取） |
| **Root Directory** | `blog` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn "app:create_app('production')"` |

4. 添加环境变量：

| Key | Value |
|-----|-------|
| `SECRET_KEY` | 随机字符串 |
| `GITHUB_REPO` | `GetBuilting/blog` |
| `GITHUB_TOKEN` | `ghp_你的Token` |
| `PYTHON_VERSION` | `3.12.0` |

5. 选 Free 计划 → **Create Web Service**

每次 `git push` 到 GitHub，Render 自动重新部署。

---

# PythonAnywhere 部署指南（推荐）

> SQLite 数据永久保留，完全免费，适合长期使用。

## 第 1 步：注册

打开 [pythonanywhere.com](https://www.pythonanywhere.com/) → 用邮箱注册 → 免费计划

## 第 2 步：打开 Bash 终端

点击顶部 **Consoles** → **Bash** → 等待终端加载

## 第 3 步：克隆代码

```bash
git clone https://github.com/GetBuilting/blog.git
cd blog/blog
```

## 第 4 步：创建虚拟环境 + 装依赖

```bash
mkvirtualenv --python=/usr/bin/python3.12 blog-env
pip install -r requirements.txt
```

> 如果没有 Python 3.12，用 `python3.10` 也可以。

## 第 5 步：配置环境变量

```bash
nano .env
```

填入（把 `你的用户名` 替换成你的 PythonAnywhere 用户名）：

```ini
SECRET_KEY=随机乱敲一串字符
GITHUB_REPO=GetBuilting/blog
GITHUB_TOKEN=ghp_你的GitHubToken
BASE_URL=https://你的用户名.pythonanywhere.com
```

`Ctrl+O` 保存，`Ctrl+X` 退出。

## 第 6 步：初始化数据库

```bash
python -c "from app import create_app; create_app()"
```

## 第 7 步：配置 Web App

1. 点击 PythonAnywhere 顶部 **Web** 标签
2. 点击 **Add a new web app** → **Manual configuration** → 选 **Python 3.12**（没 3.12 就选最新版）
3. 看到你的 Web 地址类似：`https://你的用户名.pythonanywhere.com`

4. 往下找到 **Code** 区域，编辑 **WSGI configuration file** 链接，把内容改成：

```python
import sys
import os

project_home = '/home/你的用户名/blog/blog'
os.chdir(project_home)
sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from app import create_app
application = create_app('production')
```

5. 找到 **Virtualenv** 输入框，填：`/home/你的用户名/.virtualenvs/blog-env`

6. 点击顶部绿色 **Reload** 按钮

## 第 8 步：设管理员

1. 打开你的网站 → 第一个注册的用户自动成为管理员
2. 如果不是第一个，访问：`https://你的用户名.pythonanywhere.com/first-admin`

## 以后怎么更新代码

```bash
cd ~/blog/blog
git pull origin master
```

然后在 Web 页面点 **Reload**。
