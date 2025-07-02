import os
from pprint import pprint
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
from serpapi import GoogleSearch
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_upstage import ChatUpstage

from dto.hobby import Hobby


class Hobby_recommender:

  def __init__(self, serp_api_key):
    load_dotenv()

    # 변수 선언
    self.embedding_model="embedding-query"
    self.index_name = "hobby-recommendation-chatbot"

    # Pinecone vector store 객체 생성
    self.pinecone_vectorstore = PineconeVectorStore.from_existing_index(
        index_name = self.index_name,
        embedding = UpstageEmbeddings(model=self.embedding_model),
    )

    # api key
    self.serp_api_key = serp_api_key

  def recommend(self, user_desc, user_hobby):

    # 1. 사용자 유사도 기반 1차 취미 추천
    first_results = self.pinecone_vectorstore.similarity_search(
      query=user_desc,
      k=2,
      namespace="user_descriptions",
      filter={
        "hobby" : {"$ne": user_hobby}
      }
    )

    first_recommended_hobbies = [
      Hobby(doc.metadata["hobby"], doc.metadata["hobby_eng"]) for doc in first_results
    ]

    # 2. 취미 유사도 기반 2차 취미 추천
    # 1차 추천된 취미 각각에 대해 하나씩 추가로 추천하기
    second_recommended_hobbies = []
    for hobby in first_recommended_hobbies:
      # 현재 hobby의 desc 조회
      hobby_desc = self.pinecone_vectorstore._index.fetch(
        ids=[hobby.eng_name], 
        namespace="hobby_descriptions"
      )["vectors"][hobby.eng_name]["metadata"]["text"]

      second_result = self.pinecone_vectorstore.similarity_search(
        query=hobby_desc,
        k=1,
        namespace="hobby_descriptions",
        filter={
          "hobby" : {"$ne": hobby.name}
        }
      )[0]

      second_recommended_hobbies.append(Hobby(second_result.metadata["hobby"], second_result.metadata["hobby_eng"]))

    # 1, 2차 취미 추천 리스트 병합
    recommended_hobbies = first_recommended_hobbies + second_recommended_hobbies
    print("추천 취미 리스트 : ", [hobby.name for hobby in recommended_hobbies])

    # 3. 추천 취미에 도움될 만한 정보 조회(RAG)
    params = {
      "engine": "google",
      "num": "4",
      "api_key": self.serp_api_key
    }
    
    for hobby in recommended_hobbies:
      params["q"] = f"Tell me helpful information for {hobby.eng_name} beginners"

      search = GoogleSearch(params)
      search_result = search.get_dict()

      # 검색 결과를 로드
      urls = [ result["link"] for result in search_result["organic_results"]]

      loader = UnstructuredURLLoader(urls=urls)
      data = loader.load()

      # text split
      text_splitter = RecursiveCharacterTextSplitter(
          chunk_size=200,
          chunk_overlap=50)

      splits = text_splitter.split_documents(data)

      retrieved_vectorstore = PineconeVectorStore.from_documents(
          splits, 
          UpstageEmbeddings(model=self.embedding_model), 
          index_name=self.index_name,
          namespace="retrieved_docs"
      )

      retriever = retrieved_vectorstore.as_retriever(
          search_type= 'mmr', # default : similarity(유사도) / mmr 알고리즘
          search_kwargs={
              "k": 10, # 쿼리와 관련된 chunk를 10개 검색하기 (default : 4)
              "namespace" : "retrieved_docs"
          } 
      )

      docs = retriever.invoke(f"Tell me helpful information for {hobby.eng_name} beginners")
      docs = [doc.page_content for doc in docs]

      # Prompt
      system = """
      Answer the question based on context. In Korean.
      """
      user = """
      Question: {question}
      Context: {context}

      <<<Output Format>>>
      `Answer: <Answer based on the document.>`
      """

      prompt = ChatPromptTemplate.from_messages(
          [
              ("system", system),
              ("human", user),
          ]
      )

      # LLM & Chain
      llm = ChatUpstage()
      rag_chain = prompt | llm | StrOutputParser()

      # Generate
      generation = rag_chain.invoke({"context": "\n\n".join(docs), "question": f"{hobby.name}을/를 처음 하는 사람에게 도움될만한 정보를 알려줘"})
      generation = generation.split(":")[1].strip() if ":" in generation else generation.strip()
      hobby.set_additional_info(generation)


    # 4. 추천 취미의 추가 정보 조회 => DB 연동 필요함


    # 5. 최종 반환 데이터 정제 및 반환
    return recommended_hobbies
