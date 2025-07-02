import pandas as pd
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings

# .env 파일의 환경변수 로드
load_dotenv()

aws_region = "us-east-1"
embedding_model="embedding-query"
index_name = "hobby-recommendation-chatbot"


user_desc_list = pd.read_csv("user_desc.csv").to_dict('records')
hobby_desc_list = pd.read_csv("hobbies_desc.csv").to_dict('records')

# user_desc
user_desc_docs = [ Document(
    page_content = user_desc["user_desc"],
    metadata = {
        "hobby" : user_desc["hobby"],
        "hobby_eng" : user_desc["eng_name"]
    }
) for user_desc in user_desc_list]


# hobbies_desc
hobby_desc_docs = [ Document(
    page_content = hobby_desc["description"],
    metadata = {
        "hobby" : hobby_desc["name"],
        "hobby_eng" : hobby_desc["eng_name"]
    }
) for hobby_desc in hobby_desc_list]
hobby_ids = [hobby_desc["eng_name"] for hobby_desc in hobby_desc_list]


pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# create new index
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=4096,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

# embedding - user_desc
pinecone_vectorstore = PineconeVectorStore.from_documents(
    user_desc_docs, 
    UpstageEmbeddings(model=embedding_model), 
    index_name=index_name,
    namespace="user_descriptions"
)

# embedding - hobby_desc
pinecone_vectorstore = PineconeVectorStore.from_documents(
    hobby_desc_docs, 
    UpstageEmbeddings(model=embedding_model), 
    index_name=index_name,
    namespace="hobby_descriptions",
    ids=hobby_ids
)