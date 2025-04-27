import spacy
import re
import unicodedata
import requests
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import logging

nlp = spacy.load("en_core_web_sm")

LANGUAGE_KEYWORDS = [
    "english", "vietnamese", "french", "german", "japanese", "chinese", "korean",
    "spanish", "portuguese", "italian", "russian", "arabic", "thai", "dutch",
    "hindi", "bengali", "turkish", "polish", "urdu", "indonesian", "malay",
    "swedish", "norwegian"
]

app = FastAPI(debug=True)


logging.basicConfig(level=logging.DEBUG)


class CVTextRequest(BaseModel):
    text: str


class RecommendJobsRequest(BaseModel):
    text: str
    top_k: Optional[int] = None


class RecommendCandidatesRequest(BaseModel):
    job_title: str
    description: str
    top_k: Optional[int] = None


class SearchCandidatesRequest(BaseModel):
    gender: Optional[str] = None
    experience: Optional[str] = None
    skill: Optional[str] = None
    language: Optional[str] = None
    education: Optional[str] = None
    certification: Optional[str] = None
    goal: Optional[str] = None
    top_k: Optional[int] = None


def clean_text_for_nlp(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(
        c for c in text
        if unicodedata.category(c)[0] != 'So'
        and not (unicodedata.category(c)[0] == 'C' and c not in ['\n', '\t'])
    )
    text = re.sub(r"[^\w\s.,:()@/-]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


SECTION_STOPWORDS = [
    "interest", "interests", "hobby", "hobbies",
    "reference", "references", "objective", "about me", "summary",
    "certification"
]


def extract_education_experience_skill(text: str):
    education, experience, skills = [], [], []
    lines = text.split('\n')
    current_section = None

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        if not line_clean:
            continue

        line_lower_nopunct = re.sub(r"[^\w\s]", "", line_lower)

        if any(stop in line_lower_nopunct for stop in SECTION_STOPWORDS):
            current_section = None
            continue

        if "education" in line_lower_nopunct:
            current_section = 'education'
            continue
        elif any(key in line_lower_nopunct for key in ["experience", "experiences", "work"]):
            current_section = 'experience'
            continue
        elif any(key in line_lower_nopunct for key in ["skill", "skills"]):
            current_section = 'skills'
            continue

        if current_section == 'education':
            education.append(line_clean)

        elif current_section == 'experience':
            experience.append(line_clean)

        elif current_section == 'skills':
            raw_items = re.split(r'[,\.\n]', line_clean)
            for item in raw_items:
                skill = item.strip()
                if skill and len(skill) > 1:
                    skills.append(skill)

    def dedup(seq):
        seen = set()
        return [x for x in seq if not (x in seen or seen.add(x))]

    return dedup(education), dedup(experience), dedup(skills)



def extract_languages(text: str):
    lower = text.lower()
    return list({lang for lang in LANGUAGE_KEYWORDS if lang in lower})


def query_esco_api(skill_name: str):
    try:
        url = "https://ec.europa.eu/esco/api/search"
        params = {
            "text": skill_name,
            "type": "skill",
            "language": "en"
        }
        response = requests.get(url, params=params)
        print(response.status_code)
        if response.status_code == 200:
            data = response.json()
            if "_embedded" in data and "results" in data["_embedded"]:
                return [result["title"] for result in data["_embedded"]["results"] if "title" in result]
        return []
    except Exception as e:
        print(f"[ESCO API Error] {e}")
        return []


def extract_esco_skills_from_list(skill_list: list):
    esco_skills = set()
    for skill in skill_list:
        matches = query_esco_api(skill)
        if matches:
            esco_skills.update(matches)

    if not esco_skills:
        return fallback_manual_skill_extraction(" ".join(skill_list))

    return list(esco_skills)


def fallback_manual_skill_extraction(text: str):
    fallback_keywords = {
        "it": ["python", "fastapi", "elasticsearch", "django", "react", "node.js", "java", "docker", "graphql"],
        "marketing": ["seo", "content marketing", "google analytics", "facebook ads", "social media", "email marketing"],
        "finance": ["financial analysis", "budgeting", "forecasting", "accounting", "investment", "financial modeling"],
        "management": ["project management", "leadership", "teamwork", "risk management", "agile", "scrum", "kanban"],
        "engineering": ["mechanical engineering", "civil engineering", "electrical engineering", "cad", "solidworks", "matlab"],
        "design": ["graphic design", "ui/ux", "photoshop", "illustrator", "prototyping", "wireframing"],
        "sales": ["negotiation", "sales strategy", "customer relationship management", "b2b sales", "closing deals", "lead generation"],
        "medicine": ["patient care", "clinical research", "pharmacology", "surgery", "medical equipment", "healthcare management"],
        "education": ["curriculum design", "teaching", "classroom management", "e-learning", "pedagogy", "assessment"],
        "law": ["contract law", "litigation", "corporate law", "intellectual property", "legal research", "compliance"]
    }

    text = text.lower()
    skills_found = set()

    for keywords in fallback_keywords.values():
        for keyword in keywords:
            if keyword in text:
                skills_found.add(keyword.capitalize())

    return list(skills_found)


def analyze_cv_info(text: str, email: str):
    education, experience, skill = extract_education_experience_skill(text)
    extracted_esco_skills = extract_esco_skills_from_list(skill)
    print("--skill")
    print(skill)

    return {
        "email": email,
        "education": education,
        "experience": experience,
        "languages": extract_languages(text),
        "skills": extracted_esco_skills
    }