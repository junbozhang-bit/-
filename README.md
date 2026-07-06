# AI 简历解析与匹配服务

这是一个基于 Python 的简历解析与岗位匹配服务。它支持 PDF 简历上传、文本提取、结构化简历信息抽取，以及招聘描述的关键词匹配评分。

## 目录结构

- `app/main.py` - FastAPI 后端服务
- `app/parser.py` - 简历解析与匹配逻辑
- `frontend/index.html` - 简单的前端上传与匹配页面
- `requirements.txt` - Python 依赖

## 运行方法

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 打开浏览器

访问 `http://127.0.0.1:8000/` 进行简历上传与岗位匹配测试。

## API

- `POST /api/upload` - 上传 PDF 简历并返回解析结果
- `POST /api/match` - 对已解析简历或文本简历进行岗位匹配评分
- `GET /api/resume/{resume_id}` - 查询缓存中的简历解析结果

## 说明

- 使用 `PyPDF2` 提取 PDF 文本；对简历文本进行清洗后抽取姓名、电话、邮箱、地址、教育背景、项目经历等字段。
- 匹配服务会从招聘描述中提取关键词，与简历中的技能和项目内容进行简单关键词匹配，得到匹配度评分。
- 已上传简历会基于 SHA256 哈希缓存，避免重复解析。
