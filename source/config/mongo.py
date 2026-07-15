from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class MongoService:
    def __init__(self, uri:str, db:str, collection:str):
        self.client = MongoClient(uri)
        self.collection = self.client[db][collection]

    def query(self, query : dict):
        result = self.collection.find(query)
        return list(result)
    
    def upsert_by_id(self, id, document):
        self.collection.update_one(
            filter={"_id" : id}, update=document, upsert=True
        )

def get_default_mongo_client():
    return MongoService(
        uri=os.getenv("MONGO_URI"), db=os.getenv("MONGO_DB"), collection=os.getenv("MONGO_COLLECTION")
    )