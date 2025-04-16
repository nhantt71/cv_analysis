from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=["https://open-university-sear-4132308520.ap-southeast-2.bonsaisearch.net"],
    http_auth=("3pwadlnjvm", "e82nqrvykx"),  # dùng http_auth cho elasticsearch 7.x
)


