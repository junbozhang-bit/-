"""
AI 模拟模块 — 模拟 LLM 从简历中提取结构化信息和语义匹配评分。

设计理念：
- 不依赖外部 API，用规则 + 启发式算法模拟 AI 的输出行为
- 返回结构含 confidence 字段，模拟 LLM 的置信度输出
- 匹配评分改为多维加权，替代纯关键词重叠
"""

import re
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════
# 技能语义分组 — 模拟 AI 对技能体系的"理解"
# ═══════════════════════════════════════════════════════════

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "Python 生态": ["python", "django", "flask", "fastapi", "tornado", "aiohttp", "celery", "sqlalchemy", "pydantic", "pytest", "jupyter", "numpy", "pandas", "scipy", "scikit-learn"],
    "后端通用": ["restful", "rest", "api", "graphql", "grpc", "websocket", "microservice", "微服务", "后端", "backend", "server", "nginx", "gunicorn", "uwsgi"],
    "数据库": ["mysql", "postgresql", "redis", "mongodb", "sqlite", "oracle", "sqlserver", "elasticsearch", "es", "neo4j", "influxdb", "clickhouse", "tidb", "memcached", "sql", "nosql", "orm"],
    "消息/异步": ["kafka", "rabbitmq", "mq", "redis", "celery", "asyncio", "async", "coroutine", "消息队列", "task queue"],
    "DevOps": ["docker", "kubernetes", "k8s", "jenkins", "ci/cd", "git", "gitlab", "github", "actions", "terraform", "ansible", "prometheus", "grafana", "elk", "linux", "shell", "bash"],
    "云服务": ["aws", "azure", "gcp", "aliyun", "阿里云", "腾讯云", "华为云", "serverless", "ecs", "oss", "s3", "ec2", "lambda", "函数计算", "fc", "rds"],
    "AI/ML": ["tensorflow", "pytorch", "keras", "machine learning", "deep learning", "nlp", "cv", "transformer", "bert", "gpt", "llm", "大模型", "机器学习", "深度学习", "自然语言处理", "计算机视觉", "算法", "algorithm", "模型训练", "推理", "inference", "fine-tune", "rag", "embedding", "langchain", "模型部署"],
    "前端": ["react", "vue", "angular", "javascript", "typescript", "html", "css", "node.js", "nodejs", "next.js", "nuxt", "webpack", "vite", "前端", "frontend", "bootstrap", "tailwind", "jquery"],
    "数据分析": ["数据分析", "可视化", "spark", "hadoop", "flink", "etl", "data warehouse", "hive", "airflow", "tableau", "matplotlib", "plotly", "bi", "报表"],
    "安全": ["网络安全", "web安全", "渗透", "加密", "ssl", "tls", "oauth", "jwt", "authentication", "authorization", "auth", "权限", "xss", "csrf", "sql注入", "waf"],
}

EDUCATION_LEVELS = {
    "博士": 5, "博士研究生": 5, "phd": 5, "doctor": 5,
    "硕士": 4, "硕士研究生": 4, "master": 4, "研究生": 4,
    "本科": 3, "学士": 3, "bachelor": 3, "大学": 3,
    "大专": 2, "专科": 2, "associate": 2,
    "高中": 1, "中专": 1, "high school": 1,
}

SALARY_PATTERNS = [
    re.compile(r"(?:期望|薪资|月薪|年薪|薪资要求|期望月薪|期望年薪|薪水|工资)[:：\s]*(\d+[kKwW]?\s*[-~至到]\s*\d+[kKwW]?)", re.I),
    re.compile(r"(?:期望|薪资|月薪|年薪)[:：\s]*(\d+[kK])", re.I),
    re.compile(r"(\d+[kK]\s*[-~至到]\s*\d+[kK])", re.I),
    re.compile(r"(?:期望|薪资|月薪|年薪).*?(\d{4,6}\s*[-~至到]\s*\d{4,6})"),
    re.compile(r"薪资[:：\s]*(面议|可谈|open)", re.I),
]

# ═══════════════════════════════════════════════════════════
# AI 模拟 — 简历信息提取
# ═══════════════════════════════════════════════════════════

def ai_extract_resume(text: str) -> Dict:
    """
    模拟 LLM 对简历文本的结构化信息提取。
    返回结构包含 extracted 字段和 confidence 标注。
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    extracted = {
        "basic_info": _extract_basic_info(text, lines),
        "career_info": _extract_career_info(text, lines),
        "background": _extract_background(text, lines),
        "skills_summary": _extract_skills_summary(text, lines),
    }

    return {
        "extracted": extracted,
        "model": "AI-Resume-Parser-v2 (simulated LLM)",
        "confidence": _compute_confidence(extracted),
        "analysis_note": _generate_extraction_note(extracted),
    }


def _extract_basic_info(text: str, lines: List[str]) -> Dict:
    NAME_PATTERN = re.compile(r"^[一-鿿]{2,5}$")
    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_PATTERN = re.compile(r"(?:(?:\+?86[- ]?)?(?:1[3-9]\d{9}|0\d{2,3}[- ]?\d{7,8}))")
    ADDRESS_KEYWORDS = ["地址", "居住地", "现居", "工作地点", "所在地", "住址"]

    name = None
    for line in lines[:5]:
        if NAME_PATTERN.match(line) and not any(kw in line for kw in ["年龄", "男", "女", "专业", "简历"]):
            name = line
            break
    if not name:
        for line in lines[:5]:
            if "姓名" in line:
                candidate = re.sub(r"姓名[:：\s]*", "", line).strip()
                if candidate:
                    name = candidate
                    break

    email_match = EMAIL_PATTERN.search(text)
    phone_match = PHONE_PATTERN.search(text)

    address = None
    for line in lines:
        if any(kw in line for kw in ADDRESS_KEYWORDS):
            addr = re.sub(r"(?:地址|居住地|现居|工作地点|所在地|住址)[:：\s]*", "", line).strip()
            if addr:
                address = addr
                break

    # 期望薪资
    salary = None
    for pat in SALARY_PATTERNS:
        m = pat.search(text)
        if m:
            salary = m.group(0).strip()
            break

    return {
        "name": {"value": name, "confidence": 0.90 if name else 0.0},
        "phone": {"value": phone_match.group(0) if phone_match else None, "confidence": 0.95 if phone_match else 0.0},
        "email": {"value": email_match.group(0) if email_match else None, "confidence": 0.95 if email_match else 0.0},
        "address": {"value": address, "confidence": 0.75 if address else 0.0},
        "expected_salary": {"value": salary, "confidence": 0.70 if salary else 0.0},
    }


def _extract_career_info(text: str, lines: List[str]) -> Dict:
    JOB_KEYWORDS = ["求职意向", "期望岗位", "目标岗位", "期望职位", "求职岗位", "应聘岗位"]

    job_intention = None
    for line in lines:
        if any(kw in line for kw in JOB_KEYWORDS):
            intent = re.sub(r"(?:求职意向|期望岗位|目标岗位|期望职位|求职岗位|应聘岗位)[:：\s]*", "", line).strip()
            job_intention = intent or None
            break

    if not job_intention:
        for line in lines[:10]:
            if "Python" in line or "后端" in line or "全栈" in line or "开发工程师" in line:
                job_intention = line.strip()
                break

    # 提取技能相关行
    skill_lines = []
    in_skills = False
    for line in lines:
        if "技能" in line or "技术栈" in line:
            in_skills = True
            continue
        if in_skills and (len(line) < 5 or any(kw in line for kw in ["经历", "经验", "项目", "工作", "教育"])):
            in_skills = False
            continue
        if in_skills and line:
            skill_lines.append(line)

    return {
        "job_intention": {"value": job_intention, "confidence": 0.80 if job_intention else 0.0},
        "skill_lines": skill_lines,
    }


def _extract_background(text: str, lines: List[str]) -> Dict:
    # 学历
    education = None
    edu_level = 0
    for line in lines:
        for kw, level in EDUCATION_LEVELS.items():
            if kw.lower() in line.lower():
                if level > edu_level:
                    edu_level = level
                    education = line.strip()

    # 工作年限 — 改进版
    work_years = None
    years_detail = None

    # 模式1: 显式声明 "X年工作经验"
    exp_match = re.search(r"(\d+)\s*年.*?(?:工作|经验|开发|从业)", text)
    if exp_match:
        work_years = f"{exp_match.group(1)} 年"
        years_detail = f"AI 识别：简历中明确提及 {exp_match.group(1)} 年工作经验"

    # 模式2: 从工作经历时间跨度推断
    if not work_years:
        CURRENT_YEAR = 2026
        date_ranges = re.findall(r"(20\d{2})[\.\-/年](0[1-9]|1[0-2])?\s*[-~至到]\s*(20\d{2}|至今|现在|now)", text)
        if len(date_ranges) >= 1:
            try:
                earliest = min(int(d[0]) for d in date_ranges)
                numeric_ends = [int(d[2]) for d in date_ranges if d[2] and d[2].isdigit()]
                has_now = any(d[2] in ("至今", "现在", "now") for d in date_ranges)
                # "至今"表示持续在岗，以上限年份为准（推迟到当前）
                latest = CURRENT_YEAR if has_now else (max(numeric_ends) if numeric_ends else CURRENT_YEAR)
                span = latest - earliest
                if span > 0:
                    tag = "（含至今）" if has_now else ""
                    work_years = f"约 {span} 年"
                    years_detail = f"AI 推断：基于经历时间跨度 ({earliest}-{latest}){tag}，约 {span} 年"
            except (ValueError, TypeError):
                pass

    # 模式3: 根据经历数量估算
    if not work_years:
        exp_count = len(re.findall(r"(20\d{2})[\.\-/年]", text))
        if exp_count >= 6:
            work_years = "3 年以上"
            years_detail = f"AI 推断：检测到 {exp_count} 处时间标记，推测 3 年以上经验"
        elif exp_count >= 3:
            work_years = "1-3 年"
            years_detail = f"AI 推断：检测到 {exp_count} 处时间标记，推测 1-3 年经验"

    # 项目经历
    projects = _extract_projects(text)

    return {
        "education": {"value": education, "level": edu_level, "confidence": 0.85 if education else 0.0},
        "work_years": {"value": work_years, "detail": years_detail, "confidence": 0.70 if work_years else 0.0},
        "projects": projects,
    }


def _extract_projects(text: str) -> List[Dict]:
    projects = []
    if "项目经历" not in text:
        return projects

    _, content = text.split("项目经历", 1)
    # 截取到下一个大标题
    for header in ["工作经历", "教育经历", "专业技能", "个人优势", "自我评价"]:
        if header in content:
            content = content.split(header)[0]

    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 10]

    for para in paragraphs[:6]:
        # 尝试提取项目名（第一行）
        proj_lines = para.split("\n")
        name = proj_lines[0].strip()
        desc = "\n".join(proj_lines[1:]) if len(proj_lines) > 1 else ""

        # 提取项目中的技术关键词
        tech_keywords = []
        for cat, keywords in SKILL_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in para.lower() and kw.lower() not in tech_keywords:
                    tech_keywords.append(kw.lower())

        projects.append({
            "name": name,
            "description": desc or para,
            "tech_stack": tech_keywords[:8],
        })

    return projects


def _extract_skills_summary(text: str, lines: List[str]) -> Dict:
    """技能摘要 — 按语义分类聚合"""
    text_lower = text.lower()

    skill_categories_found = {}
    all_skills = []

    for category, keywords in SKILL_CATEGORIES.items():
        matched = [kw for kw in keywords if kw.lower() in text_lower]
        if matched:
            skill_categories_found[category] = matched
            all_skills.extend(matched)

    # 去重
    seen = set()
    all_skills_unique = []
    for s in all_skills:
        if s not in seen:
            seen.add(s)
            all_skills_unique.append(s)

    # 推测技术栈（基于出现最多的类别）
    primary_stack = []
    for cat, skills in sorted(skill_categories_found.items(), key=lambda x: -len(x[1])):
        primary_stack.append(cat)

    return {
        "categories": skill_categories_found,
        "all_skills": all_skills_unique[:40],
        "primary_stack": primary_stack[:4],
        "skill_count": len(all_skills_unique),
    }


def _compute_confidence(extracted: Dict) -> Dict:
    """计算各维度提取置信度"""
    conf = {}

    # 基本信息置信度
    basic = extracted.get("basic_info", {})
    basic_conf = []
    for field in ["name", "phone", "email"]:
        if basic.get(field, {}).get("value"):
            basic_conf.append(1.0)
        else:
            basic_conf.append(0.0)
    conf["basic_info"] = round(sum(basic_conf) / len(basic_conf), 2) if basic_conf else 0

    # 背景信息置信度
    bg = extracted.get("background", {})
    bg_conf = 0.5
    if bg.get("education", {}).get("value"):
        bg_conf += 0.25
    if bg.get("work_years", {}).get("value"):
        bg_conf += 0.25
    conf["background"] = round(min(bg_conf, 1.0), 2)

    # 技能置信度
    skills = extracted.get("skills_summary", {})
    skill_count = skills.get("skill_count", 0)
    conf["skills"] = round(min(skill_count / 15, 1.0), 2)

    conf["overall"] = round((conf["basic_info"] * 0.4 + conf["background"] * 0.3 + conf["skills"] * 0.3), 2)

    return conf


def _generate_extraction_note(extracted: Dict) -> str:
    """模拟 AI 对提取结果的分析评注"""
    notes = []
    basic = extracted.get("basic_info", {})

    if basic.get("name", {}).get("value"):
        notes.append(f"识别到候选人：{basic['name']['value']}")
    if basic.get("expected_salary", {}).get("value"):
        notes.append(f"期望薪资：{basic['expected_salary']['value']}")

    bg = extracted.get("background", {})
    edu = bg.get("education", {}).get("value", "")
    if edu:
        notes.append(f"学历背景：{edu}")

    wy = bg.get("work_years", {}).get("value", "")
    if wy:
        notes.append(f"工作经验：{wy}")

    skills = extracted.get("skills_summary", {})
    stack = skills.get("primary_stack", [])
    if stack:
        notes.append(f"核心技术方向：{' > '.join(stack[:2])}")

    if not notes:
        notes.append("简历信息较为简略，建议完善关键信息以提高匹配准确度。")

    return "；".join(notes)


# ═══════════════════════════════════════════════════════════
# AI 模拟 — 简历与岗位匹配评分
# ═══════════════════════════════════════════════════════════

def ai_match_score(parsed_resume: Dict, job_description: str) -> Dict:
    """
    模拟 LLM 对简历与岗位需求的语义匹配评分。
    返回多维度分项得分和分析说明。
    """
    resume_text = parsed_resume.get("text", "")
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    # ── 1. 技能匹配度 (权重 0.45) ──
    skill_score, skill_detail = _score_skill_match(resume_lower, job_lower)

    # ── 2. 经验匹配度 (权重 0.25) ──
    experience_score, exp_detail = _score_experience_match(parsed_resume, job_lower)

    # ── 3. 学历匹配度 (权重 0.15) ──
    education_score, edu_detail = _score_education_match(parsed_resume, job_lower)

    # ── 4. 行业/领域匹配度 (权重 0.15) ──
    domain_score, domain_detail = _score_domain_match(resume_lower, job_lower)

    # ── 加权总分 ──
    weights = {"skill": 0.45, "experience": 0.25, "education": 0.15, "domain": 0.15}
    total_score = (
        skill_score * weights["skill"]
        + experience_score * weights["experience"]
        + education_score * weights["education"]
        + domain_score * weights["domain"]
    )
    total_score = round(min(total_score, 1.0), 4)

    # ── 生成 AI 分析 ──
    analysis = _generate_match_analysis(total_score, skill_score, experience_score, education_score, domain_score, skill_detail, exp_detail, edu_detail)

    return {
        "match_score": round(total_score * 100, 2),
        "score_breakdown": {
            "skill_match": {"score": round(skill_score * 100, 2), "weight": 45, "detail": skill_detail},
            "experience_match": {"score": round(experience_score * 100, 2), "weight": 25, "detail": exp_detail},
            "education_match": {"score": round(education_score * 100, 2), "weight": 15, "detail": edu_detail},
            "domain_match": {"score": round(domain_score * 100, 2), "weight": 15, "detail": domain_detail},
        },
        "analysis": analysis,
        "score_level": _score_level(total_score),
        "model": "AI-Match-Engine-v2 (simulated LLM)",
    }


def _score_skill_match(resume_lower: str, job_lower: str) -> Tuple[float, str]:
    job_categories = {}
    resume_categories = {}

    for category, keywords in SKILL_CATEGORIES.items():
        job_hits = [kw for kw in keywords if kw.lower() in job_lower]
        resume_hits = [kw for kw in keywords if kw.lower() in resume_lower]
        if job_hits:
            job_categories[category] = job_hits
        if resume_hits:
            resume_categories[category] = resume_hits

    if not job_categories:
        return 0.0, "岗位描述未检测到明确技能关键词"

    category_scores = []
    for cat, job_kws in job_categories.items():
        resume_kws = resume_categories.get(cat, [])
        if resume_kws:
            matched = set(job_kws) & set(resume_kws)
            ratio = len(matched) / len(job_kws)
            category_scores.append(ratio)
        else:
            category_scores.append(0.0)

    avg_score = sum(category_scores) / len(category_scores) if category_scores else 0.0

    # 增加简历技能覆盖率作为加分
    total_job_skills = sum(len(v) for v in job_categories.values())
    total_resume_skills = sum(len(v) for v in resume_categories.values())
    coverage_bonus = min(total_resume_skills / max(total_job_skills, 1), 1.0) * 0.15

    final_score = min(avg_score + coverage_bonus, 1.0)

    matched_cats = [c for c in job_categories if c in resume_categories]
    detail = f"岗位需求涵盖 {len(job_categories)} 个技能分类，简历匹配 {len(matched_cats)} 个：{', '.join(matched_cats[:4]) or '无'}"
    if len(matched_cats) < len(job_categories):
        missing = [c for c in job_categories if c not in resume_categories]
        detail += f"；缺失：{', '.join(missing[:3])}"

    return final_score, detail


def _score_experience_match(parsed_resume: Dict, job_lower: str) -> Tuple[float, str]:
    resume_years = _parse_years_from_resume(parsed_resume)
    job_years = _parse_years_from_job(job_lower)

    if job_years is None:
        # 岗位没写年限要求，根据简历情况给基准分
        return 0.70, "岗位未明确年限要求，默认基准 70%"

    if resume_years is None:
        return 0.30, "无法从简历中确定工作年限，AI 乐观估计 30%"

    if resume_years >= job_years:
        if resume_years >= job_years * 2:
            return 1.0, f"简历 {resume_years} 年 ≥ 要求 {job_years} 年（超额满足）"
        return 0.90, f"简历 {resume_years} 年 ≥ 要求 {job_years} 年"
    else:
        ratio = resume_years / job_years
        if ratio >= 0.7:
            return 0.65, f"简历 {resume_years} 年，接近要求 {job_years} 年（{round(ratio*100)}%）"
        elif ratio >= 0.5:
            return 0.45, f"简历 {resume_years} 年，低于要求 {job_years} 年（{round(ratio*100)}%）"
        else:
            return 0.25, f"简历 {resume_years} 年，远低于要求 {job_years} 年"


def _parse_years_from_resume(parsed_resume: Dict) -> Optional[float]:
    wy = parsed_resume.get("background", {}).get("work_years", "")
    if not wy:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", str(wy))
    if match:
        val = float(match.group(1))
        return val

    # 文字描述映射
    text = str(wy).lower()
    if "应届" in text or "实习" in text:
        return 0.0
    if "1-3" in text or "一到三" in text:
        return 2.0
    if "3-5" in text or "三到五" in text:
        return 4.0
    if "5" in text or "五" in text:
        return 5.0

    return None


def _parse_years_from_job(job_lower: str) -> Optional[float]:
    patterns = [
        (r"(\d+)\s*[-~至到]\s*(\d+)\s*年.*?(?:经验|工作)", lambda m: (float(m.group(1)) + float(m.group(2))) / 2),
        (r"(\d+)\s*年.*?(?:以上|及以上).*?(?:经验|工作)", lambda m: float(m.group(1)) + 1),
        (r"(\d+)\s*年.*?(?:经验|工作)", lambda m: float(m.group(1))),
        (r"(?:应届|实习).*?(?:优先|也可|均可|亦可)", lambda m: 0.0),
        (r"经验不限", lambda m: None),
    ]

    for pattern, extractor in patterns:
        m = re.search(pattern, job_lower)
        if m:
            result = extractor(m)
            return result

    return None


def _score_education_match(parsed_resume: Dict, job_lower: str) -> Tuple[float, str]:
    resume_edu = parsed_resume.get("background", {}).get("education", "")
    if not resume_edu:
        return 0.50, "未检测到学历信息，默认 50%"

    resume_level = 0
    for kw, level in EDUCATION_LEVELS.items():
        if kw.lower() in str(resume_edu).lower():
            resume_level = max(resume_level, level)

    job_level = 0
    for kw, level in EDUCATION_LEVELS.items():
        if kw.lower() in job_lower:
            job_level = max(job_level, level)

    if job_level == 0:
        return 0.80, "岗位未明确学历要求，简历有学历记录，默认 80%"

    if resume_level >= job_level:
        if resume_level > job_level:
            return 1.0, "学历水平超过岗位要求"
        return 0.90, "学历水平满足岗位要求"
    elif resume_level == job_level - 1:
        return 0.60, "学历略低于岗位要求（差一档）"
    else:
        return 0.30, f"学历低于岗位要求（差 {job_level - resume_level} 档）"


def _score_domain_match(resume_lower: str, job_lower: str) -> Tuple[float, str]:
    """行业/领域匹配"""
    DOMAIN_KEYWORDS = {
        "AI/机器学习": ["ai", "机器学习", "深度学习", "人工智能", "llm", "大模型", "nlp", "cv", "算法", "模型"],
        "科学计算": ["科学计算", "hpc", "simulation", "仿真", "分子动力学", "量子化学", "蛋白", "生物信息"],
        "云计算": ["cloud", "云", "serverless", "saas", "paas", "iaas", "分布式"],
        "金融": ["金融", "fintech", "银行", "证券", "支付", "风控", "交易"],
        "电商": ["电商", "商城", "订单", "支付", "物流", "库存", "商品"],
        "企业服务": ["企业", "erp", "crm", "oa", "办公", "内部", "管理系统"],
        "大数据": ["大数据", "数据仓库", "数据湖", "etl", "spark", "hadoop"],
        "物联网": ["iot", "物联网", "嵌入式", "传感器", "边缘计算"],
    }

    job_domains = set()
    resume_domains = set()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in job_lower:
                job_domains.add(domain)
                break
        for kw in keywords:
            if kw.lower() in resume_lower:
                resume_domains.add(domain)
                break

    if not job_domains:
        return 0.70, "岗位未明确行业/领域方向"

    if not resume_domains:
        return 0.40, "未从简历检测到行业/领域特征"

    overlap = job_domains & resume_domains
    if overlap:
        score = len(overlap) / len(job_domains)
        return min(score + 0.2, 1.0), f"行业匹配：{', '.join(overlap)}"
    else:
        return 0.30, f"行业方向有差异：岗位偏向 {', '.join(list(job_domains)[:2])}"


def _score_level(score: float) -> str:
    if score >= 0.80:
        return "优秀"
    elif score >= 0.65:
        return "良好"
    elif score >= 0.50:
        return "中等"
    elif score >= 0.35:
        return "偏低"
    else:
        return "较低"


def _generate_match_analysis(total: float, skill: float, exp: float, edu: float, domain: float,
                             skill_d: str, exp_d: str, edu_d: str) -> str:
    level = _score_level(total)
    parts = [f"【{level}】综合匹配度 {round(total * 100)}%。"]

    if skill >= 0.70:
        parts.append("技能匹配度较高，核心技能栈与岗位需求吻合。")
    elif skill >= 0.40:
        parts.append("部分技能匹配，建议补充岗位所需的关键技能。")
    else:
        parts.append("技能覆盖不足，需要重点学习岗位要求的技术栈。")

    if exp >= 0.70:
        parts.append("工作经验满足或超出岗位要求。")
    elif exp >= 0.40:
        parts.append("工作经验略低于岗位要求，但具备基础。")
    else:
        parts.append("工作经验与岗位要求有较大差距。")

    if edu >= 0.70:
        parts.append("学历背景符合或超出要求。")
    elif edu >= 0.50:
        parts.append("学历基本满足要求。")

    parts.append(f"（{skill_d}）")
    parts.append(f"（{exp_d}）")

    return "".join(parts)
