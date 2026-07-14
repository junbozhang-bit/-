import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.ai_agent import ai_extract_resume, ai_match_score

NAME_PATTERN = re.compile(r"^[一-鿿]{2,5}$")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?:(?:\+?86[- ]?)?(?:1[3-9]\d{9}|0\d{2,3}[- ]?\d{7,8}))")
ADDRESS_KEYWORDS = ["地址", "居住地", "现居", "工作地点", "所在地", "住址"]
EDUCATION_KEYWORDS = ["本科", "硕士", "博士", "大专", "高中", "中专"]
JOB_INTENTION_KEYWORDS = ["求职意向", "期望岗位", "目标岗位", "期望职位", "求职岗位"]
SECTION_HEADERS = ["教育经历", "专业技能", "项目经历", "工作经历", "个人优势", "联系方式"]

STOPWORDS = {
    "和", "与", "及", "的", "了", "在", "可", "能", "有", "为", "项目", "工作", "经验", "能力", "技术", "开发", "系统",
    "实现", "管理", "完成", "使用", "包括", "基于", "支持", "数据", "服务", "后台", "前端", "后端",
}

SALARY_PATTERNS = [
    re.compile(r"(?:期望|薪资|月薪|年薪|薪资要求|期望月薪|期望年薪|薪水|工资)[:：\s]*(\d+[kKwW]?\s*[-~至到]\s*\d+[kKwW]?)", re.I),
    re.compile(r"(?:期望|薪资|月薪|年薪)[:：\s]*(\d+[kK])", re.I),
    re.compile(r"(\d+[kK]\s*[-~至到]\s*\d+[kK])", re.I),
    re.compile(r"(?:期望|薪资|月薪|年薪).*?(\d{4,6}\s*[-~至到]\s*\d{4,6})"),
    re.compile(r"薪资[:：\s]*(面议|可谈|open)", re.I),
]


def compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    from io import BytesIO
    from PyPDF2 import PdfReader

    stream = BytesIO(file_bytes)
    reader = PdfReader(stream)
    text_blocks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_blocks.append(page_text)
    return "\n".join(text_blocks)


def clean_text(text: str) -> str:
    cleaned = text.replace("\xa0", " ")
    cleaned = cleaned.replace("　", " ")
    cleaned = cleaned.replace("\\n", "\n")
    cleaned = cleaned.replace("", "•")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
    lines = [line.strip() for line in cleaned.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def split_sections(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    sections: Dict[str, List[str]] = {}
    current_title = "正文"
    sections[current_title] = []

    for line in lines:
        trimmed = line.strip()
        if trimmed in SECTION_HEADERS:
            current_title = trimmed
            sections[current_title] = []
            continue
        sections[current_title].append(line)

    return {title: "\n".join(body).strip() for title, body in sections.items()}


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_PATTERN.search(text)
    return match.group(0) if match else None


def extract_name(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:5]:
        if NAME_PATTERN.match(line) and not any(keyword in line for keyword in ["年龄", "男", "女", "专业", "简历"]):
            return line
    for line in lines[:5]:
        if "姓名" in line:
            candidate = re.sub(r"姓名[:：\s]*", "", line).strip()
            if candidate:
                return candidate
    return None


def extract_address(text: str) -> Optional[str]:
    for line in text.splitlines():
        if any(keyword in line for keyword in ADDRESS_KEYWORDS):
            address = re.sub(r"(?:地址|居住地|现居|工作地点|所在地|住址)[:：\s]*", "", line).strip()
            if address:
                return address
    return None


def extract_education(text: str) -> Optional[str]:
    for line in text.splitlines():
        if any(keyword in line for keyword in EDUCATION_KEYWORDS):
            return line.strip()
    return None


def extract_project_experiences(text: str) -> List[str]:
    if "项目经历" not in text:
        return []
    _, project_area = text.split("项目经历", 1)
    paragraphs = [p.strip() for p in project_area.split("\n\n") if p.strip()]
    return paragraphs[:5]


def extract_expected_salary(text: str) -> Optional[str]:
    """从简历中提取期望薪资"""
    for pat in SALARY_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0).strip()
    return None


def infer_work_years(text: str) -> Optional[str]:
    dates = re.findall(r"(20\d{2})[.\-/年](0[1-9]|1[0-2])?(?:[.\-/年](20\d{2})[.\-/年](0[1-9]|1[0-2])?)?", text)
    if dates:
        return f"{len(dates)} 项/段经验"
    if "年" in text and "工作" in text:
        return "已具备相关工作经验"
    return None


def extract_job_intention(text: str) -> Optional[str]:
    for line in text.splitlines():
        if any(keyword in line for keyword in JOB_INTENTION_KEYWORDS):
            intent = re.sub(r"(?:求职意向|期望岗位|目标岗位|期望职位|求职岗位)[:：\s]*", "", line).strip()
            return intent or None
    top_skill_line = next((line for line in text.splitlines() if "Python" in line or "后端" in line or "全栈" in line), None)
    return top_skill_line.strip() if top_skill_line else "Python 后端/全栈开发"


def extract_keywords(text: str, limit: int = 50) -> List[str]:
    tokens = re.findall(r"[一-鿿]+|[A-Za-z0-9_+-]+", text)
    cleaned = [token.strip().lower() for token in tokens if len(token.strip()) > 1]
    filtered = [token for token in cleaned if token not in STOPWORDS]
    unique = []
    for word in filtered:
        if word not in unique:
            unique.append(word)
    return unique[:limit]


# ═══════════════════════════════════════════════════════════
# 核心解析函数 — 集成 AI 模拟模块
# ═══════════════════════════════════════════════════════════

def parse_resume(file_bytes: bytes) -> Dict[str, object]:
    raw_text = extract_text_from_pdf_bytes(file_bytes)
    text = clean_text(raw_text)
    sections = split_sections(text)

    # ── 传统正则提取 ──
    basic_info = {
        "name": extract_name(text),
        "phone": extract_phone(text),
        "email": extract_email(text),
        "address": extract_address(text),
        "expected_salary": extract_expected_salary(text),
    }
    background = {
        "education": extract_education(text),
        "work_years": infer_work_years(text),
        "projects": extract_project_experiences(text),
    }
    career = {
        "job_intention": extract_job_intention(text),
        "skills": sections.get("专业技能", ""),
        "education": sections.get("教育经历", basic_info.get("education") or ""),
        "projects": sections.get("项目经历", ""),
    }

    # ── AI 模拟提取（增强模式） ──
    ai_result = ai_extract_resume(text)
    ai_extracted = ai_result.get("extracted", {})
    ai_confidence = ai_result.get("confidence", {})

    # 用 AI 结果增强：工作年限详情、技能分类、项目技术栈
    ai_background = ai_extracted.get("background", {})
    enhanced_work_years = ai_background.get("work_years", {}).get("value")
    work_years_detail = ai_background.get("work_years", {}).get("detail", "")

    ai_skills = ai_extracted.get("skills_summary", {})
    skills_categories = ai_skills.get("categories", {})
    primary_stack = ai_skills.get("primary_stack", [])

    # 用 AI 提取的项目（含技术栈标注）
    ai_projects = ai_background.get("projects", [])

    return {
        "resume_id": compute_hash(file_bytes),
        "text": text,
        "basic_info": basic_info,
        "background": {
            **background,
            "work_years": enhanced_work_years or background.get("work_years"),
            "work_years_detail": work_years_detail,
            "projects": background.get("projects"),
            "ai_projects_detail": ai_projects,
        },
        "career": career,
        "keywords": extract_keywords(text),
        "sections": sections,
        # ── AI 增强字段 ──
        "ai_analysis": {
            "note": ai_result.get("analysis_note", ""),
            "confidence": ai_confidence,
            "skill_categories": {cat: list(skills)[:8] for cat, skills in skills_categories.items()},
            "primary_stack": primary_stack,
        },
    }


# ═══════════════════════════════════════════════════════════
# 核心匹配函数 — 集成 AI 模拟模块
# ═══════════════════════════════════════════════════════════

def compute_match(parsed_resume: Dict[str, object], job_description: str) -> Dict[str, object]:
    # ── 传统关键词提取（保留用于前端展示） ──
    job_description = clean_text(job_description)
    job_keywords = extract_keywords(job_description, limit=60)
    resume_keywords = parsed_resume.get("keywords", [])

    skill_text = parsed_resume.get("career", {}).get("skills", "")
    skill_keywords = extract_keywords(skill_text, limit=60)
    project_text = parsed_resume.get("career", {}).get("projects", "")
    project_keywords = extract_keywords(project_text, limit=60)

    all_resume_keywords = set(resume_keywords + skill_keywords + project_keywords)
    matched_full = [keyword for keyword in job_keywords if keyword in all_resume_keywords]

    base_score = len(matched_full) / max(len(job_keywords), 1)
    education_bonus = 0.05 if parsed_resume.get("background", {}).get("education") else 0
    experience_bonus = 0.05 if parsed_resume.get("background", {}).get("work_years") else 0
    keyword_score = round(min(1.0, base_score + education_bonus + experience_bonus) * 100, 2)

    # ── AI 模拟语义匹配评分（主评分） ──
    ai_match_result = ai_match_score(parsed_resume, job_description)

    return {
        "resume_id": parsed_resume.get("resume_id"),
        # 传统关键词数据
        "job_keywords": job_keywords,
        "matched_keywords": matched_full,
        "matched_count": len(matched_full),
        "job_keyword_count": len(job_keywords),
        "keyword_match_score": keyword_score,
        # ── AI 多维评分（主评分） ──
        "match_score": ai_match_result.get("match_score"),
        "score_breakdown": ai_match_result.get("score_breakdown"),
        "analysis": ai_match_result.get("analysis"),
        "score_level": ai_match_result.get("score_level"),
        # 简历片段（供前端展示）
        "skill_text": skill_text,
        "project_text": project_text,
    }
