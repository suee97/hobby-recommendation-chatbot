# 필요한 라이브러리는 pip install -r requirements.txt로 간단하게 설치할 수 있습니다.
# 가상환경 설정이 필요하다면 notion의 python 가상환경 설정을 참고해주세요.
# 추가: .env 파일에 SOLAR_LLM_API_KEY = '받은 API KEY' 추가해주세요.

import os
from pprint import pprint
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
import serpapi
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_upstage import ChatUpstage

from dto.hobby import Hobby
from db.hobby_query import get_hobby_by_name


class Hobby_recommender:

  def __init__(self, serp_api_key):
    load_dotenv()

    # 변수 선언
    self.embedding_model="solar-embedding-1-large-passage"
    self.index_name = "hobby-recommendation-chatbot"

    # Pinecone vector store 객체 생성
    self.pinecone_vectorstore = PineconeVectorStore.from_existing_index(
        index_name = self.index_name,
        embedding = UpstageEmbeddings(model=self.embedding_model),
    )

    # api key
    self.serp_api_key = serp_api_key

  def recommend(self, user_desc, user_hobby):
    hobby_filter = [user_hobby]

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
    hobby_filter += [doc.metadata["hobby"] for doc in first_results]

    # 2. 취미 유사도 기반 2차 취미 추천
    # 1차 추천된 취미 각각에 대해 하나씩 추가로 추천하기
    second_recommended_hobbies = []
    for hobby in first_recommended_hobbies:
      print("다음 추천에서 제외될 취미 목록 : ", hobby_filter)

      # 현재 hobby의 desc 조회
      hobby_desc = self.pinecone_vectorstore._index.fetch(
        ids=[hobby.eng_name], 
        namespace="hobby_descriptions"
      ).vectors[hobby.eng_name]["metadata"]["text"]

      # desc 세팅
      hobby.set_desc(hobby_desc)

      second_result = self.pinecone_vectorstore.similarity_search(
        query=hobby_desc,
        k=1,
        namespace="hobby_descriptions",
        filter={
          "hobby" : {"$nin": hobby_filter}
        }
      )[0]

      print(second_result)

      new_hobby = Hobby(second_result.metadata["hobby"], second_result.metadata["hobby_eng"])
      new_hobby.set_desc(second_result.page_content)
      second_recommended_hobbies.append(new_hobby)

      # 필터 대상으로 추가
      hobby_filter.append(new_hobby.name)



    # 1, 2차 취미 추천 리스트 병합
    recommended_hobbies = first_recommended_hobbies + second_recommended_hobbies
    print("추천 취미 리스트 : ", [hobby.name for hobby in recommended_hobbies])

    for hobby in recommended_hobbies:
      hobby.set_image(get_hobby_by_name(hobby.name)[0])

    return recommended_hobbies


  def search_additional_info(self, hobby_name):

    # hobby 객체 생성
    hobby = Hobby(hobby_name, None)

    # 추천 취미의 추가 정보 조회 
    hobby_info = get_hobby_by_name(hobby.name)

    hobby.set_image(hobby_info[0])
    hobby.set_desc(hobby_info[1])
    hobby.set_detail(hobby_info[2])
    hobby.set_equipments(hobby_info[3])

    # 추천 취미에 도움될 만한 정보 조회(RAG)
    params = {
      "engine": "google",
      "num": "10",
      "api_key": self.serp_api_key
    }
    
    print("="*30)
    print(f"{hobby} 검색중 ...")
    params["q"] = f"{hobby.eng_name} beginner tips"

    search = serpapi.search(params)
    search_result = search.as_dict()

    # 1. organic_results 우선
    urls = []
    if "organic_results" in search_result and search_result["organic_results"]:
        urls = [result["link"] for result in search_result["organic_results"]]

    # 3. 그래도 없으면 안내 메시지
    if not urls:
        print("검색 결과에 사용할 수 있는 링크가 없습니다:", search_result)
        # 예외를 발생시키지 않고, 안내 메시지나 빈 결과로 처리
        hobby.set_additional_info("검색 결과가 충분하지 않습니다. 구글/유튜브/포럼 등에서 직접 정보를 찾아보세요.")
        return hobby
    
    loader = UnstructuredURLLoader(urls=urls[:2])
    data = loader.load()

    # text split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50
    )

    splits = text_splitter.split_documents(data)
    print("chunk count : ", len(splits))

    batch_size = 100
    for i in range(0, len(splits), batch_size):
      batch = splits[i:i+batch_size]
      PineconeVectorStore.from_documents(
          batch, 
          UpstageEmbeddings(model=self.embedding_model), 
          index_name=self.index_name,
          namespace="retrieved_docs"
      )

    retrieved_vectorstore = PineconeVectorStore(
        embedding=UpstageEmbeddings(model=self.embedding_model),
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
    You must answer in Korean.
    Assume the user is a beginner who enjoys this hobby, and provide information that would be helpful for them.
    Share places where they can get help, useful websites, or related knowledge.
    Answer in a friendly tone and always respond in Korean.

    Important:
    - Never include error messages, access denied notices, advertisements, or irrelevant text (for example: 'on this server', 'Access Denied', 'Reference #', 'Forbidden', 'Not Found', etc.) in your answer.
    - Only summarize and deliver information that is genuinely helpful for beginners.
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

    # 5. 최종 반환 데이터 정제 및 반환
    return hobby
