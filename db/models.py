from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    detail = Column(String)
    experience = Column(String)