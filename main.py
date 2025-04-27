from typing import Optional

from fastapi import Request
from fastapi import FastAPI
from pydantic import BaseModel
from utils.parser import analyze_cv_info
from utils.embedding import generate_embedding
from es import es
from scipy.spatial.distance import cosine
from db.job_postgres_module import get_all_jobs
from utils.parser import clean_text_for_nlp
import sys
import json
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

import logging
logging.basicConfig(level=logging.DEBUG)


class CVTextRequest(BaseModel):
    text: str


class RecommendJobsRequest(BaseModel):
    text: str
    top_k: Optional[int] = None


class RecommendCandidatesRequest(BaseModel):
    job_title: str
    description: str
    top_k: Optional[int] = 1000


class SearchCandidatesRequest(BaseModel):
    gender: Optional[str] = None
    experience: Optional[str] = None
    skill: Optional[str] = None
    language: Optional[str] = None
    education: Optional[str] = None
    certification: Optional[str] = None
    goal: Optional[str] = None
    top_k: Optional[int] = None




@app.get("/")
def hello_world():
    return {"Hello": "World"}



@app.post("/parse-cv")
def parse_cv_text(request: CVTextRequest, req: Request):
    try:
        email = req.query_params.get("email")
        cleaned_text = clean_text_for_nlp(request.text)

        result = analyze_cv_info(cleaned_text, email)

        formatted_result = {
            "status": "success",
            "data": {
                "email": email,
                "education": result["education"],
                "experience": result["experience"],
                "languages": result["languages"],
                "skills": result["skills"]
            }
        }

        print(json.dumps(formatted_result, indent=4))

        text = f"{result['skills']} {result['experience']} {result['education']} {result['languages']}"
        vector = generate_embedding(text)

        es.index(
            index="cv_index",
            body={**result, "cv_vector": vector}
        )

        return formatted_result
    except Exception as e:
        return {"error": str(e)}


def cosine_similarity(v1, v2):
    return 1 - cosine(v1, v2)


@app.get("/recommend-jobs")
def recommend_jobs_for_candidate(email: str, top_k: int = 30):
    res = es.search(index="cv_index", body={
        "query": {
            "term": {
                "email": email
            }
        }
    })


    if not res["hits"]["hits"]:
        return {"error": "CV not found for this email."}

    cv_vector = res["hits"]["hits"][0]["_source"]["cv_vector"]

    jobs = get_all_jobs()

    #Calculate similarity
    scored_jobs = []
    for job in jobs:
        job_text = f"{job['detail']} {job['experience']}"
        job_vector = generate_embedding(job_text)

        similarity = cosine_similarity(cv_vector, job_vector)

        if similarity > 0.2:
            scored_jobs.append({
                **job,
                "similarity": similarity
            })

    top_jobs = sorted(scored_jobs, key=lambda x: x["similarity"], reverse=True)[:top_k]

    return {
        "recommended_jobs": top_jobs
    }



@app.get("/recommend-candidates")
def recommend_candidates(req: RecommendCandidatesRequest):
    text = f"{req.job_title} {req.description}"
    vector = generate_embedding(text)

    knn_query = {
        "knn": {
            "field": "cv_vector",
            "query_vector": vector,
            "k": 100,
            "num_candidates": 100
        }
    }

    res = es.search(index="cv_index", body={
        "size": req.top_k,
        "_source":{
            "excludes": ["cv_vector"]
        },
        "query": knn_query
    })

    return {
        "recommended_candidates": [hit["_source"] for hit in res["hits"]["hits"]]
    }


@app.post("/search-candidates")
def search_candidates(req: SearchCandidatesRequest):
    search_text = " ".join([
        req.experience or "",
        req.skill or "",
        req.language or "",
        req.education or "",
        req.certification or "",
        req.goal or ""
    ]).strip()

    if not search_text:
        return {"error": "At least one search field must be provided."}

    vector = generate_embedding(search_text)

    knn_query = {
        "knn": {
            "field": "cv_vector",
            "query_vector": vector,
            "k": 100,
            "num_candidates": 100
        }
    }

    res = es.search(index="cv_index", body={
        "size": req.top_k or 1000,
        "_source": {
            "excludes": ["cv_vector"]
        },
        "query": knn_query
    })

    return {
        "matched_candidates": [hit["_source"] for hit in res["hits"]["hits"]]
    }
