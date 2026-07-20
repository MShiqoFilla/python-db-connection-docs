from dotenv import load_dotenv
from typing import Literal
import boto3
import os

load_dotenv()

class S3Service:
    """
    S3 Client Instance, 
    Must receive these kwargs:
    ---
        - s3_host
        - s3_port
        - s3_access_key
        - s3_secret_key
        - s3_bucket
    """
    def __init__(self, **s3_configs):
        self.s3_host = s3_configs['s3_host']
        self.s3_port = s3_configs['s3_port']
        self.s3_access_key = s3_configs['s3_access_key']
        self.s3_secret_key = s3_configs['s3_secret_key']
        self.s3_bucket_name = s3_configs['s3_bucket']

        self.client = self.connect()

    def connect(self):
        try:
            return boto3.client(
                "s3",
                endpoint_url = f"http://{self.s3_host}:{self.s3_port}",
                aws_access_key_id=self.s3_access_key,         
                aws_secret_access_key=self.s3_secret_key
            )
        except Exception as e:
            print(f"Failed to connect to S3 :: {e}")
    
    def check_file_path_exists(self, s3_path: str) -> bool:
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        try:
            self.client.head_object(Bucket=self.s3_bucket_name, Key=key_path)
            return True
        except Exception as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise

    def read_json(self, s3_path : str) -> str: #resulted document in form json dumps string
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        try:
            s3obj = self.client.get_object(Bucket = self.s3_bucket_name, Key = key_path)
            if key_path.endswith(("json", "jsonl")):
                document = s3obj["Body"].read().decode('utf-8')
                return document
        except UnicodeDecodeError as e:
            raise e

    def put_json(self, s3_path: str, content: str | bytes):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        if not isinstance(content, (str, bytes)): 
            raise Exception('content s3 is only str or bytes')
        self.client.put_object(Bucket=self.s3_bucket_name, Key=key_path, Body=content, ContentType="application/json")
    
    def put_append_jsonl(self, s3_path: str, content: str | bytes) -> None:
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        if not isinstance(content, (str, bytes)): 
            raise Exception('content s3 is only str or bytes')
        check_exists = self.check_file_path_exists(key_path)
        if check_exists:
            content = self.read_json(s3_path) + "\n" + content
        self.client.put_object(Bucket=self.s3_bucket_name, Key=key_path, Body=content)

    def upload(self, file_path, s3_path):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        self.client.upload_file(file_path, self.s3_bucket_name, key_path)
    
    def download(self, s3_path, file_path):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        self.client.download_file(self.s3_bucket_name, key_path, file_path)

    def list_all_child_folders(self, s3_path: str):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        if not key_path.endswith('/'):
            key_path = key_path + '/'
        response = self.client.list_objects_v2(Bucket=self.s3_bucket_name, Prefix=key_path, Delimiter='/')
        return [data['Prefix'] for data in response.get('CommonPrefixes', [])]
    
    def list_files(self, s3_path: str, type: Literal["key", "metadata"] = "key"):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        response = self.client.list_objects_v2(Bucket=self.s3_bucket_name, Prefix=key_path)
        contents = response.get('Contents', [])
        if type == "metadata":
            return contents
        elif type == "key":
            return [data['Key'] for data in contents]

    def list_all_files(self, s3_path: str, type: Literal["key", "metadata"] = "key"):
        key_path = s3_path.replace(f's3://{self.s3_bucket_name}/', '')
        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=self.s3_bucket_name, Prefix=key_path)
        all_contents = []
        for page in page_iterator:
            if 'Contents' in page:
                all_contents.extend(page['Contents'])
        if type == "metadata":
            return all_contents
        elif type == "key":
            return [data['Key'] for data in all_contents]
        
    # def read_shapefile_to_gdf(self, s3_path_prefix: str):
    #     import tempfile
    #     import geopandas
    #     shp_files_to_download = self.list_all_files(s3_path_prefix)
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         for key in shp_files_to_download:
    #             filename = os.path.basename(key)
    #             file_path = os.path.join(temp_dir, filename)
    #             self.download(key, file_path)

    #         shp_files = [f for f in os.listdir(temp_dir) if f.endswith('.shp')]
    #         shp_file = shp_files[0]
    #         shp_path = os.path.join(temp_dir, shp_file)
    #         gdf = gpd.read_file(shp_path)
    #     return gdf

def get_default_s3_client():
    return S3Service(
        s3_host=os.getenv("S3_HOST"),
        s3_port=os.getenv("S3_PORT"),
        s3_access_key=os.getenv("S3_ACCESS_KEY"),
        s3_secret_key=os.getenv("S3_SECRET_KEY"),
        s3_bucket=os.getenv("S3_BUCKET")
    )