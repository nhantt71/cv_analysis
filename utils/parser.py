import spacy

nlp = spacy.load("en_core_web_sm")


LANGUAGE_KEYWORDS = [
    "english", "vietnamese", "french", "german", "japanese", "chinese", "korean",
    "spanish", "portuguese", "italian", "russian", "arabic", "thai", "dutch",
    "hindi", "bengali", "turkish", "polish", "urdu", "indonesian", "malay",
    "swedish", "norwegian"
]

SKILL_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "php", "ruby", "go", "swift",
    "react", "angular", "vue", "next.js", "django", "flask", "spring", "fastapi", "node.js",
    "express", "tailwind", "bootstrap", "laravel", "docker", "kubernetes", "jenkins", "aws",
    "azure", "gcp", "terraform", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "hadoop", "spark", "git", "jira", "excel", "figma", "agile", "scrum",
    "communication", "leadership", "problem-solving"
]


def analyze_cv_info(text: str):
    doc = nlp(text)
    lower_text = text.lower()

    result = {
        "email": None,
        "education": [],
        "experience": [],
        "skills": [],
        "languages": []
    }

    # --- Education & Experience ---
    for sent in doc.sents:
        lower = sent.text.lower()
        if any(w in lower for w in ["bachelor", "master", "university", "phd", "education", "degree"]):
            result["education"].append(sent.text.strip())
        elif any(w in lower for w in ["experience", "responsibilities", "worked at", "intern", "role", "project"]):
            result["experience"].append(sent.text.strip())

    # --- Skills: keyword + noun chunks ---
    found_skills = set()
    for chunk in doc.noun_chunks:
        for skill in SKILL_KEYWORDS:
            if skill in chunk.text.lower():
                found_skills.add(skill)
    for skill in SKILL_KEYWORDS:
        if skill in lower_text:
            found_skills.add(skill)
    result["skills"] = list(found_skills)

    # --- Languages ---
    found_languages = set()
    for lang in LANGUAGE_KEYWORDS:
        if lang in lower_text:
            found_languages.add(lang)
    result["languages"] = list(found_languages)

    return result