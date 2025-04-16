from typing import Optional

from fastapi import FastAPI
from fastapi.params import Body, Query
from pydantic import BaseModel
from utils.parser import analyze_cv_info
from utils.embedding import generate_embedding
from es import es
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

@app.post("/parse-cv")
def parse_cv_text(request: CVTextRequest = Body(...), email: str = Query(...)):

    result = analyze_cv_info(request.text)

    result["email"] = email

    # Generate embedding from key CV sections
    text = f"{result['skills']} {result['experience']} {result['education']} {result['languages']}"
    vector = generate_embedding(text)

    # Store in Elasticsearch (single operation)
    es.index(
        index="cv_index",
        body={
            **result,
            "cv_vector": vector
        }
    )

    es(result)
    return {
        "status": "success",
        "data": result
    }

@app.post("/recommend-jobs")
def recommend_jobs(req: RecommendJobsRequest):
    query_vector = generate_embedding(req.text)

    knn_query = {
        "knn": {
            "job_vector": {
                "vector": query_vector,
                "k": 1000,  # lấy nhiều nhất có thể để tìm tương đồng cao
                "num_candidates": 1000
            }
        }
    }

    result = es.search(index="job_index", body={
        "size": req.top_k or 1000,
        "query": knn_query
    })

    return {
        "recommended_jobs": [hit["_source"] for hit in result["hits"]["hits"]]
    }



@app.post("/recommend-candidates")
def recommend_candidates(req: RecommendCandidatesRequest):
    text = f"{req.job_title} {req.description}"
    vector = generate_embedding(text)

    knn_query = {
        "knn": {
            "cv_vector": {
                "vector": vector,
                "k": 1000,  # số lượng lớn để tìm gần như tất cả
                "num_candidates": 1000
            }
        }
    }

    res = es.search(index="cv_index", body={
        "size": req.top_k or 1000,  # nếu req.top_k là None → lấy tất cả
        "query": knn_query
    })

    return {
        "recommended_candidates": [hit["_source"] for hit in res["hits"]["hits"]]
    }

