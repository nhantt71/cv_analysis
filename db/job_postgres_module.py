from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, func
from models.job_model import Job
from typing import List, Dict

# Init engine and session
engine = create_engine("postgresql://postgres:Admin%40123@localhost:5432/jobdb")

def get_all_jobs() -> List[Dict]:
    with Session(engine) as session:
        now = func.now()
        jobs = session.query(Job).filter(
            Job.end_date > now,
            Job.enable == True
        ).all()
        return [
            {
                "id": job.id,
                "name": job.name,
                "enable": job.enable,
                "detail": job.detail,
                "experience": job.experience
            }
            for job in jobs
        ]
