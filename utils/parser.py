import re
import spacy

nlp = spacy.load("en_core_web_sm")

def analyze_cv_info(text: str):
    doc = nlp(text)
    result = {
        "email": None,
        "education": [],
        "experience": [],
        "skills": [],
        "languages": []
    }


    #Skills
    skill_lines = [line for line in text.lower().split("\n") if "skill" in line]
    if skill_lines:
        result["skills"] = list(set(re.findall(r"\b[A-Za-z]{2,}\b", "\n".join(skill_lines))))[:10]

    #Experience
    result["experience"] = [
        sent.text for sent in doc.sents
        if any(word in sent.text.lower() for word in ["experience", "worked", "responsibilities"])
    ]

    #Education
    result["education"] = [
        sent.text for sent in doc.sents
        if any(word in sent.text.lower() for word in ["bachelor", "university", "degree", "education"])
    ]

    #Language
    language_section = [line for line in text.split("\n") if "language" in line.lower()]
    if language_section:
        result["languages"] = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)?\b', language_section[0])

    return result
