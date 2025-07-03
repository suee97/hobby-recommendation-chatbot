# 다음 명령어로 설치 필요
# pip install fastapi uvicorn openai python-dotenv

# 이제 pip install -r requirements.txt로 간단하게 설치할 수 있습니다.
# 가상환경 설정이 필요하다면 notion의 python 가상환경 설정을 참고해주세요.
# 추가: .env 파일에 SOLAR_LLM_API_KEY = '받은 API KEY' 추가해주세요.

import os, random, string, json, time, json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from datetime import datetime, timedelta
from recommend_hobby import Hobby_recommender

# 새로 추가된 모듈 import
from hobby_service import HobbyRecommendationService
from util.llm_tools import llm_functions
from recommend_hobby import get_hobby_by_name
from dto.hobby import Hobby

app = FastAPI() 

app.mount("/static", StaticFiles(directory="./static"), name="static")

@app.on_event("startup")
async def startup_event():
    global hobby_recommender
    hobby_recommender = Hobby_recommender(os.getenv("SERPAPI_API_KEY"))

@app.get("/")
def root():
    return {"message": "FastAPI 서버 정상적으로 실행 중"}

# API KEY 불러오기
load_dotenv()
SOLAR_LLM_API_KEY = os.getenv('SOLAR_LLM_API_KEY')

# Solar LLM
client = OpenAI(
    api_key=SOLAR_LLM_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

# 취미 추천 서비스 초기화
hobby_service = HobbyRecommendationService()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 'python app.py' 실행시 서버 열도록 하는 코드
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# 세션 관리 - 기존 구조 유지하되 취미 추천 데이터 추가
chat_storage = {
    'test-token': [[], datetime(2099, 1, 1, 0, 0)],
    'old-token': [[], datetime(2025, 6, 1, 12, 0)],
}

# Model
class ChatRequestModel(BaseModel):
    token: str
    message: str

class HobbyRecommenderModel(BaseModel):
    token : str
    user_desc : str
    user_hobby : str


# API
@app.get("/generate-token")
def generate_token():
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choice(characters) for _ in range(20))
    if token not in chat_storage:
        # 기존 구조에 취미 추천 데이터 추가
        session_data = hobby_service.create_session_data()
        session_data[1] = datetime.now()  # timestamp 설정
        chat_storage[token] = session_data
    return {"statusCode": 200, "data": {"token": token}}


@app.post("/chat")
def chat_post(req: ChatRequestModel):

    # 세션 30분 넘은 값들 지우기 (기존 로직 유지)
    chat_storage[req.token][1] = datetime.now()
    expire_delta = timedelta(minutes=30)
    keys_to_delete = []
    for token, data in chat_storage.items():
        if datetime.now() - data[1] > expire_delta:
            keys_to_delete.append(token)
    for token in keys_to_delete:
        del chat_storage[token]

    # 토큰 존재하는지 확인, 없으면 에러
    if req.token not in chat_storage:
        return {"statusCode": 400, "errorMessage": "서버에 존재하지 않는 토큰입니다."}
    
    # 세션 데이터 가져오기
    session_data = chat_storage[req.token]
    history = session_data[0]
    
    # 첫 대화일 때 시스템 프롬프트 추가
    if len(history) == 0:
        history.append({"role": "system", "content": hobby_service.get_system_prompt()})
    
    # 사용자 메시지 추가
    newChat = {"role": "user", "content": req.message}
    history.append(newChat)

    # Solar LLM에 요청 보내고 응답 받기
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "tendency_chat",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "assistant chat response"
                    },
                    "summary": {
                        "type": "string",
                        "description": "user tendency summary. (if completed)"
                    },
                    "recommended_hobby": {
                        "type": "string",
                        "description": "user tendency summary. (if completed)"
                    },
                    "question_count": {
                        "type": "number",
                        "description": "number of question"
                    },
                    "is_completed": {
                        "type": "boolean",
                        "description": "if completly grasp user tendency, then true else false"
                    }
                },
                "required": ["message", "summary", "recommended_hobby", "question_count", "is_completed"]
            }
        }
    }

    response = client.chat.completions.create(
        model = "solar-mini",
        messages = history,
        response_format = response_format,
        # stream = True,
    )
    answerStr = response.choices[0].message.content
    answer = json.loads(response.choices[0].message.content)
    print(answer)

    # AI 응답을 히스토리에 추가
    history.append({"role": "assistant", "content": answerStr})

    # 성향 파악 미완료시
    if answer["is_completed"] is False:
        return {
            "statusCode": 200,
            "data": {
                "message": answer["message"],
                "question_count": answer["question_count"],
                "is_complete": answer["is_completed"]
            }
        }
    
    recommend_req = HobbyRecommenderModel(
        token=req.token,
        user_desc=answer["summary"],
        user_hobby= answer["recommended_hobby"]
    )
    print(f"-- 성향 파악 완료, 취미 추천 시작 (취미 썸네일만 해당)")
    start = time.perf_counter()
    result = recommend_post(recommend_req)
    end = time.perf_counter()
    print(f"-- 취미 추천 실행 시간: {end - start:.4f}초")
    return {"statusCode": 200, "data": {"recommend_result": result}}
    

@app.post("/recommend-hobby")
def recommend_post(req: HobbyRecommenderModel):
    result = hobby_recommender.recommend(req.user_desc, req.user_hobby)
    return result


@app.get("/recommend-hobby/{hobby}")
def get_hobby_additional_info(hobby: str):
    print(f"-- {hobby} 정보 조회 및 RAG 시작")
    start = time.perf_counter()
    hobbyDto = Hobby(hobby, None)
    hobby_info = get_hobby_by_name(hobby)
    hobbyDto.set_image(hobby_info[0])
    hobbyDto.set_desc(hobby_info[1])
    hobbyDto.set_detail(hobby_info[2])
    hobbyDto.set_equipments(hobby_info[3])
    hobbyDto.set_eng_name(hobby_info[4])
    additional_info = hobby_recommender.search_additional_info(hobby)
    hobbyDto.set_additional_info(additional_info)
    end = time.perf_counter()
    print(f"-- {hobby} 정보 조회 및 RAG 끝: {end - start:.4f}초")
    return hobbyDto


# 추가 API: 사용자 데이터 조회
@app.get("/user-data/{token}")
def get_user_data(token: str):
    """사용자 데이터 조회 API"""
    if token not in chat_storage:
        return {"statusCode": 400, "errorMessage": "서버에 존재하지 않는 토큰입니다."}
    
    session_data = chat_storage[token]
    return {"statusCode": 200, "data": {
        "user_data": session_data[2],
        "question_count": session_data[3],
        "is_profiling_done": session_data[4]
    }}


# 추가 API: 검색 데이터 업데이트
@app.get("/db/update")
def db_update():
    hobby_recommender.clear_db()
    hobby_recommender.update_newly_data()