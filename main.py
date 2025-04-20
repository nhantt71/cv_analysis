from typing import Optional

from fastapi import Request
from fastapi import FastAPI
from pydantic import BaseModel
from utils.parser import analyze_cv_info
from utils.embedding import generate_embedding
from es import es
from scipy.spatial.distance import cosine
from db.job_postgres_module import get_all_jobs

app = FastAPI()


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


@app.post("/parse-cv")
def parse_cv_text(request: CVTextRequest, req: Request):
    email = req.query_params.get("email")

    result = analyze_cv_info(request.text)

    # Generate embedding from key CV sections
    text = f"{result['skills']} {result['experience']} {result['education']} {result['languages']}"
    vector = generate_embedding(text)

    # Store in Elasticsearch (single operation)
    es.index(
        index="cv_index",
        body={
            **result,
            "email": email,
            "cv_vector": vector
        }
    )

    return {
        "status": "success",
        "data": result
    }


def cosine_similarity(v1, v2):
    return 1 - cosine(v1, v2)


@app.get("/recommend-jobs")
def recommend_jobs_for_candidate(email: str, top_k: int = 10):
    # 1. Lấy vector CV từ Elasticsearch theo email
    res = es.search(index="cv_index", body={
        "query": {
            "term": {
                "email.keyword": email
            }
        }
    })

    if not res["hits"]["hits"]:
        return {"error": "CV not found for this email."}

    cv_vector = res["hits"]["hits"][0]["_source"]["cv_vector"]

    # 2. Lấy tất cả job từ PostgreSQL
    jobs = get_all_jobs()  # [{id, detail, experience, ...}, ...]

    # 3. Tính similarity
    scored_jobs = []
    for job in jobs:
        job_text = f"{job['detail']} {job['experience']}"
        job_vector = generate_embedding(job_text)

        similarity = cosine_similarity(cv_vector, job_vector)
        scored_jobs.append({
            **job,
            "similarity": similarity
        })

    # 4. Sắp xếp và lấy top_k
    top_jobs = sorted(scored_jobs, key=lambda x: x["similarity"], reverse=True)[:top_k]

    return {
        "recommended_jobs": top_jobs
    }


@app.post("/recommend-candidates")
def recommend_candidates(req: RecommendCandidatesRequest):
    text = f"{req.job_title} {req.description}"
    vector = generate_embedding(text)

    knn_query = {
        "knn": {
            "cv_vector": {
                "vector": vector,
                "k": 1000,
                "num_candidates": 1000
            }
        }
    }

    res = es.search(index="cv_index", body={
        "size": req.top_k or 1000,
        "query": knn_query
    })

    return {
        "recommended_candidates": [hit["_source"] for hit in res["hits"]["hits"]]
    }


@app.post("/search-candidates")
def search_candidates(req: SearchCandidatesRequest):
    search_text = " ".join([
        req.gender or "",
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
            "cv_vector": {
                "vector": vector,
                "k": 1000,
                "num_candidates": 1000
            }
        }
    }

    res = es.search(index="cv_index", body={
        "size": req.top_k or 1000,
        "query": knn_query
    })

    return {
        "matched_candidates": [hit["_source"] for hit in res["hits"]["hits"]]
    }
