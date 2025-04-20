from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


def index_cv_data(data: dict, index: str = "cv_index"):
    es.index(index=index, body=data)