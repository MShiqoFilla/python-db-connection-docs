from elasticsearch7 import Elasticsearch
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import requests
import os

load_dotenv()

class ElasticService:
    def __init__(self, **es_configs) -> None:
        required = ["host", "port", "username", "password"]
        missing = [k for k in required if k not in es_configs]
        if missing:
            raise ValueError(f"Missing Required for custom ES Config: {', '.join(missing)}")
        self.es_host = es_configs["es_host"]
        self.es_port = es_configs["es_port"]
        self.es_user = es_configs["es_user"]
        self.es_pass = es_configs["es_pass"]

        self.client = self.connect_es()

    def get_es_metadata(self) -> str:
        url = f"http://{self.es_host}:{self.es_port}"
        response = requests.get(url, auth=HTTPBasicAuth(self.es_uname, self.es_password))
        if response.status_code == 200:
            return response.json()
        response.raise_for_status()

    def connect_es(self) -> Elasticsearch:
        try:
            if self.es_uname:
                es = Elasticsearch(
                    f"http://{self.es_host}:{self.es_port}", 
                    http_auth=(self.es_user, self.es_pass), 
                    request_timeout=30, max_retries=4
                )
            else:
                es = Elasticsearch(f"http://{self.es_host}:{self.es_port}", request_timeout=30, max_retries=4)
            return es
        except Exception as e:
            print(f"Not Connected to ES {e}")

    def info(self):
        return self.client.info()

    def get_all_indices(self, full_metadata = False):
        if full_metadata:
            return self.client.cat.indices(format="json")
        else:
            indices_metadata = self.client.cat.indices(format="json")
            return sorted([index["index"] for index in indices_metadata if not index["index"].startswith(".")])

    def get_mapping(self, index_name):
        return self.client.indices.get_mapping(index=index_name)
    
    def get_doc_by_id(self, index_name, id):
        return self.client.get(index=index_name, id=id)
    
    def ingest(self, index_name, id, doc):
        self.client.index(index=index_name, id=id, document=doc)
        return True
    
    def ingest_bulk(self, actions, chunk_size=100):
        failed = 0
        for ok, response in self.streaming_bulk(
            client=self.client, 
            chunk_size=chunk_size, 
            actions=actions, 
            request_timeout=3600
        ):
            if not ok:
                print(f"Failed to index: {response}")
                failed += 1
        print(f"Indexed counter: Success = {len(actions)-failed}, Failed = {failed}")

    def update_doc(self, index_name, id, doc):
        self.client.update(index=index_name, id=id, body={"doc" : doc})
        return True

    def search_by_ids(self, index_name:str, list_ids : list[str]):
        search = self.client.search(
            index = index_name,
            body = {
                "query" : {
                    "bool" : {
                        "filter" : {
                            "terms" : {
                                "_id" : list_ids
                            }
                        }
                    }
                },
                "size" : 1000
            },
            request_timeout=30
        )
        results = search["hits"]["hits"]
        return results
    
    def search_by_query(self, index_name: str, query: dict):
        results = self.client.search(
            index = index_name,
            body = query
        )
        return results["hits"]["hits"]
    
    def delete_by_id(self, index_name: str, id:str):
        self.client.delete(index=index_name, id=id)
        return True
    
    def scroll_by_query(self, index_name: str, query: dict, scroll_time = "2m", doc_per_scroll:int=1000, max_doc:int=None) -> list[dict]:
        response = self.client.search(
            index=index_name,
            scroll=scroll_time,
            size=doc_per_scroll,
            body=query
        )
        
        scroll_id, all_hits = response['_scroll_id'], response['hits']['hits']
        while True:
            response = self.client.scroll(
                scroll_id=scroll_id,
                scroll=scroll_time
            )
            hits = response['hits']['hits']
            all_hits.extend(hits)
            if not hits:
                break
            if max_doc:
                if len(all_hits) >= max_doc:
                    break

        self.client.clear_scroll(scroll_id=scroll_id)
        return all_hits

    def aggregate(self, index_name: str, body: dict):
        results = self.client.search(
            index = index_name,
            body = body
        )
        return results["aggregations"]
    
def get_default_es_client():
    return ElasticService(
        es_host=os.getenv("ES_HOST"), es_port=os.getenv("ES_PORT"), es_user=os.getenv("ES_USER"), es_pass=os.getenv("ES_PASS")
    )