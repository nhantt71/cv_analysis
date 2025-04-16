from elasticsearch import Elasticsearch

es = Elasticsearch(
    "https://open-university-sear-4132308520.ap-southeast-2.bonsaisearch.net:443",
    http_auth=("3pwadlnjvm", "e82nqrvykx")
)

def index_cv_data(data: dict, index: str = "cv_index"):
    es.index(index=index, body=data)


