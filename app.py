# 다음 명령어로 설치 필요
# pip install fastapi uvicorn openai python-dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import os, random, string
from datetime import datetime, timedelta

app = FastAPI() 

# API KEY 불러오기
load_dotenv()
SOLAR_LLM_API_KEY = os.getenv('SOLAR_LLM_API_KEY')

# Solar LLM
client = OpenAI(
    api_key=SOLAR_LLM_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

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

# 세션 관리
chat_storage = {
    'test-token': [[], datetime(2099, 1, 1, 0, 0)],
    'old-token': [[], datetime(2025, 6, 1, 12, 0)],
}

# Model
class ChatRequestModel(BaseModel):
    token: str
    message: str

# API
@app.get("/generate-token")
def generate_token():
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choice(characters) for _ in range(20))
    if token not in chat_storage:
        chat_storage[token] = [[], datetime.now()]
    return {"statusCode": 200, "data": {"token": token}}

@app.post("/chat")
def chat_post(req: ChatRequestModel):
    # 토큰 존재하는지 확인, 없으면 에러
    if req.token not in chat_storage:
        return {"statusCode": 400, "errorMessage": "서버에 존재하지 않는 토큰입니다."}
    
    # 토큰 있으면 이전 대화 불러오고 저장하기
    history = chat_storage[req.token][0]
    newChat = {"role": "user", "content": req.message}
    history.append(newChat)

    # 요청 보내고 응답 받기
    stream = client.chat.completions.create(
        model = "solar-mini",
        messages = history,
        stream = True,
    )
    answer = ''
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
    history.append({"role": "assistant", "content": answer})
    chat_storage[req.token][1] = datetime.now()

    # 세션 30분 넘은 값들 지우기
    expire_delta = timedelta(minutes=30)
    keys_to_delete = []
    for token, (history, saved_time) in chat_storage.items():
        if datetime.now() - saved_time > expire_delta:
            keys_to_delete.append(token)
    for token in keys_to_delete:
        del chat_storage[token]

    return {"statusCode": 200, "data": {"answer": answer}}


    # 있으면 llm에 보내기
    # 성향 파악 끝인지 확인

    return {"statusCode": 200, "data": {"미구현": "미구현"}}
