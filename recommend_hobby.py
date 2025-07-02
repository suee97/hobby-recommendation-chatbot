# 필요한 라이브러리는 pip install -r requirements.txt로 간단하게 설치할 수 있습니다.
# 가상환경 설정이 필요하다면 notion의 python 가상환경 설정을 참고해주세요.
# 추가: .env 파일에 SOLAR_LLM_API_KEY = '받은 API KEY' 추가해주세요.

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
      "num": "5",
      "api_key": self.serp_api_key
    }
    
    for hobby in recommended_hobbies:
      print("="*30)
      print(f"{hobby} 검색중 ...")
      params["q"] = f"{hobby.eng_name} beginner tips"

      search = GoogleSearch(params)
      search_result = search.get_dict()

      # 검색 결과를 로드
      if "organic_results" not in search_result:
        print("SerpAPI 응답:", search_result)
        raise Exception(f"SerpAPI 결과에 'organic_results'가 없습니다: {search_result}")

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

      docs = retriever.invoke(
          f"Tell me helpful information for {hobby.eng_name} beginners"
        )
      docs = [doc.page_content for doc in docs]

      # Prompt
      system = """
      You must answer in Korean. Think of the user as a beginner who enjoys this hobby, and provide information that would be helpful to them. Share places where they can get help, websites, or related knowledge. Answer in a friendly tone and respond in Korean.
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


    
    # 임시 - retrieved_docs 네임스페이스 삭제
    # try:
    #     self.pinecone_index.delete(namespace="retrieved_docs")
    #     print("retrieved_docs 네임스페이스가 성공적으로 삭제되었습니다.")
    # except Exception as e:
    #     print(f"네임스페이스 삭제 중 오류 발생: {e}")

    # 5. 최종 반환 데이터 정제 및 반환
    return recommended_hobbies
