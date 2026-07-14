# AI 简历解析与匹配服务

这是一个基于 Python 的简历解析与岗位匹配服务，支持 PDF 简历上传、文本提取、结构化简历信息抽取，以及招聘描述关键词匹配评分。

## 项目架构

该项目采用前后端分离结构：

- `frontend/index.html`：前端静态页面，提供简历上传、文本输入和结果展示功能。
- `app/main.py`：FastAPI 后端入口，负责接收请求、调用解析逻辑、返回 JSON 结果。
- `app/parser.py`：简历解析与岗位匹配核心模块，包含 PDF 文本提取、简历字段抽取和关键词匹配评分。
- `requirements.txt`：依赖列表，便于环境安装和部署。

## 技术选型

- Python 3.x：后端服务语言，开发效率高、生态成熟。
- FastAPI：轻量级 Web 框架，支持异步接口、自动文档和高性能。
- PyPDF2：PDF 文本提取库，用于读取简历中的文本内容。
- SHA256 哈希缓存：用于避免重复处理已上传简历，提高性能。

## 功能说明

- PDF 简历上传与文本提取
- 简历结构化信息抽取：姓名、电话、邮箱、地址、教育背景、项目经历等
- 招聘描述关键词匹配：提取岗位需求关键词，与简历内容进行简单匹配评分
- 缓存处理：基于简历内容哈希判断是否已处理过，避免重复解析

## 部署方式

### 本地开发部署

1. 创建虚拟环境：

```bash
python -m venv venv
```

2. 激活虚拟环境：

Windows:

```powershell
venv\Scripts\activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. 在浏览器中访问：

```text
http://127.0.0.1:8000/
```

### 生产部署建议

- 使用 `uvicorn` 或 `gunicorn` 作为 ASGI 服务器
- 将后端部署到云服务器或容器环境（如 Docker、Kubernetes）
- 使用反向代理服务器（如 Nginx）对外提供 HTTPS
- 按需扩展缓存与存储策略，提高并发性能

## 使用说明

### 界面操作

1. 打开浏览器访问服务地址。
2. 在前端页面中选择要上传的 PDF 简历。
3. 提交后，后端会解析简历文本并返回结构化结果。
4. 若输入岗位描述或关键词，系统将返回匹配评分结果。

### API 接口

- `POST /api/upload`

  - 功能：上传 PDF 简历并返回解析结果。
  - 请求：表单文件上传。
  - 返回：简历解析后的 JSON 数据。
- `POST /api/match`

  - 功能：对已解析简历或文本简历进行岗位匹配评分。
  - 请求：JSON 格式的岗位描述或简历文本。
  - 返回：匹配评分与匹配详情。
- `GET /api/resume/{resume_id}`

  - 功能：查询缓存中的简历解析结果。
  - 请求：简历 ID。
  - 返回：缓存结果或解析记录

## 目录结构

- `app/main.py` - FastAPI 后端服务入口
- `app/parser.py` - 简历解析与匹配逻辑实现
- `frontend/index.html` - 简单前端上传与展示页面
- `requirements.txt` - Python 项目依赖
