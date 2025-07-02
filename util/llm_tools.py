# backend/llm_tools.py

recommend_hobby_function = {
    "name": "recommend_hobby",
    "description": "취미 추천 대화의 각 단계를 구조화된 데이터로 반환합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "사용자에게 보여줄 질문이나 대화, 또는 완료 메시지"
            },
            "user_data": {
                "type": "object",
                "description": "수집된(또는 완성된) 사용자 데이터"
            },
            "question_count": {
                "type": "integer",
                "description": "현재 질문 번호(또는 전체 질문 수)"
            },
            "is_complete": {
                "type": "boolean",
                "description": "질문이 모두 끝났는지 여부"
            },
            "summary": {
                "type": "string",
                "description": "성향 요약 7문장 (질문 완료 시에만 포함)",
            },
            "recommended_hobby": {
                "type": "string",
                "description": "추천 취미명 (질문 완료 시에만 포함)",
            }
        },
        "required": ["message", "user_data", "question_count", "is_complete"]
    }
}

llm_functions = [recommend_hobby_function]