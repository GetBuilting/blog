# PythonAnywhere 部署指南

## 第 1 步：注册并创建 Web App

1. 注册 [pythonanywhere.com](https://www.pythonanywhere.com)（免费账号）
2. 打开 **Consoles** → **Bash** 终端

## 第 2 步：克隆项目

```bash
# 克隆你的仓库（替换为你的 GitHub 仓库地址）
git clone https://github.com/你的用户名/mini_mall.git

cd mini_mall
```

## 第 3 步：创建虚拟环境并安装依赖

```bash
# PythonAnywhere 使用 Python 3.12
mkvirtualenv --python=/usr/bin/python3.12 mini_mall_env

# 激活虚拟环境
workon mini_mall_env

# 安装依赖
pip install -r requirements.txt
```

## 第 4 步：配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
SECRET_KEY=生成一个随机字符串
GITHUB_REPO=你的用户名/你的仓库名
GITHUB_TOKEN=ghp_你的GitHub_Token
BASE_URL=https://你的用户名.pythonanywhere.com
EOF
```

## 第 5 步：初始化数据库

```bash
python -c "from app import create_app; app = create_app(); print('DB created')"
```

## 第 6 步：配置 Web App

1. 回到 PythonAnywhere 主页 → **Web** 标签
2. 点击 **Add a new web app**
3. 选择 **Manual configuration** → **Python 3.12**
4. 编辑 **WSGI configuration file**：

```python
import sys
import os

# 项目路径
project_home = '/home/你的用户名/mini_mall'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 加载 .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Flask app
from app import create_app
application = create_app('production')
```

5. **Virtualenv** 路径填写：`/home/你的用户名/.virtualenvs/mini_mall_env`

6. **Static files** 配置：
   - URL: `/static/`
   - Path: `/home/你的用户名/mini_mall/static/`

7. 点击顶部绿色 **Reload** 按钮

## 第 7 步：访问博客

打开 `https://你的用户名.pythonanywhere.com`

## 更新代码

每次更新代码后：

```bash
cd ~/mini_mall
git pull
workon mini_mall_env
pip install -r requirements.txt
# 点击 Web 页面上的 Reload 按钮
```

---

## 注意事项

- 免费账号每 3 个月需登录一次保持活跃
- 免费账号的站点可以被公开访问
- 视频文件过大可能加载慢，建议压缩到 5MB 以内
- SQLite 数据库文件存储在 PythonAnywhere 服务器上
