from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean

Base = declarative_base()

class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    enable = Column(Boolean)
    detail = Column(String)
    experience = Column(String)
    end_date = Column(DateTime)