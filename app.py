# 다음 명령어로 설치 필요
# pip install fastapi uvicorn openai python-dotenv

# 이제 pip install -r requirements.txt로 간단하게 설치할 수 있습니다.
# 가상환경 설정이 필요하다면 notion의 python 가상환경 설정을 참고해주세요.
# 추가: .env 파일에 SOLAR_LLM_API_KEY = '받은 API KEY' 추가해주세요.

from fastapi import FastAPI
import json
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import os, random, string
from datetime import datetime, timedelta
from recommend_hobby import Hobby_recommender

# 새로 추가된 모듈 import
from hobby_service import HobbyRecommendationService
from util.llm_tools import llm_functions

app = FastAPI() 

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

    stream = client.chat.completions.create(
        model = "solar-mini",
        messages = history,
        response_format = response_format,
        stream = True,
    )
    answer = ''
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
    print(answer)
    # arguments_str = response.choices[0].message.function_call.arguments
    # result = json.loads(arguments_str)
    
    # =================== [ AI 답변 확인 코드 ] ===================
    # print("\n" + "="*60)
    # print("🤖 AI의 원본 답변:", answer)
    # print("="*60 + "\n")
    # ==========================================================


    # AI 응답을 히스토리에 추가
    history.append({"role": "assistant", "content": answer})

    return {"d":"dd"}
    ####################################################

    # AI 응답 파싱 및 세션 데이터 업데이트
    response_data, summary, recommended_hobby = hobby_service.parse_ai_response(answer)
    
    if response_data:
        # 사용자 데이터 업데이트
        if "user_data" in response_data:
            session_data[2].update(response_data["user_data"])
        # 질문 카운트 업데이트
        if "question_count" in response_data:
            session_data[3] = response_data["question_count"]
        # 완료 상태 업데이트
        if "is_complete" in response_data:
            session_data[4] = response_data["is_complete"]
    else:
        # 파싱 실패 시 예외 처리 (예: 사용자에게 재질문 유도)
        response_data = {"is_complete": False, "message": "죄송해요, 답변을 이해하지 못했어요. 다시 한번 말씀해주시겠어요?"}
        summary = ""
        recommended_hobby = ""
    
    # 타임스탬프 업데이트
    session_data[1] = datetime.now()

    # 세션 30분 넘은 값들 지우기 (기존 로직 유지)
    expire_delta = timedelta(minutes=30)
    keys_to_delete = []
    for token, data in chat_storage.items():
        if datetime.now() - data[1] > expire_delta:
            keys_to_delete.append(token)
    for token in keys_to_delete:
        del chat_storage[token]


    # 대화 종료 전
    if response_data["is_complete"] is not None and not response_data["is_complete"]:
        return {"statusCode": 200, "data": {
            "response_data": response_data,
            "message": response_data["message"],
            "is_complete": response_data["is_complete"],
            "summary": summary,
            "recommended_hobby": recommended_hobby,
        }}
    
    # 대화 종료
    else:
        recommend_req = HobbyRecommenderModel(
            token=req.token,
            user_desc=summary,
            user_hobby="none"
        )
        result = recommend_post(recommend_req)
        return {"statusCode": 200, "data": {"recommend_result": result}}


    

@app.post("/recommend-hobby")
def recommend_post(req: HobbyRecommenderModel):
    # 토큰 존재하는지 확인, 없으면 에러
    # if req.token not in chat_storage:
    #     return {"statusCode": 400, "errorMessage": "서버에 존재하지 않는 토큰입니다."}

    hobby_recommender = Hobby_recommender(os.getenv("SERPAPI_API_KEY"))
    result = hobby_recommender.recommend(req.user_desc, req.user_hobby)


    return result
    # 응답 데이터 구성
    response = {
        "answer": answer,
        "user_data": session_data[2],
        "question_count": session_data[3],
        "is_profiling_done": session_data[4]
    }
    
    # 완료된 경우 추가 정보 포함
    if summary:
        response["summary"] = summary
    if recommended_hobby:
        response["recommended_hobby"] = recommended_hobby

    return {"statusCode": 200, "data": response}

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