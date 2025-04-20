from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from models import Job
from typing import List, Dict

# Init engine and session
engine = create_engine("postgresql://postgres:Admin%40123@localhost:5432/jobdb")

def get_all_jobs() -> List[int]:
    with Session(engine) as session:
        job_ids = session.query(Job.id).all()
        return [job_id[0] for job_id in job_ids]
