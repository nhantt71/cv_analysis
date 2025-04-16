from elasticsearch import Elasticsearch

es = Elasticsearch(
    "https://open-university-sear-4132308520.ap-southeast-2.bonsaisearch.net",
    http_auth=("3pwadlnjvm", "e82nqrvykx")
)

# Kiểm tra kết nối
try:
    print(es.info())
except Exception as e:
    print("❌ Elasticsearch connection failed:", e)
