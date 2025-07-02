import json
from typing import Dict, Tuple, Optional

class HobbyRecommendationService:
    """취미 추천을 위한 사용자 성향 분석 서비스"""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 사용자의 성향을 파악하여 취미를 추천하는 AI입니다. 

**역할:**
사용자와 자연스러운 대화를 통해 성향을 파악하고, 최종적으로 적합한 취미를 추천합니다.

**진행 방식:**
1. 총 15개의 질문을 통해 사용자의 성향을 파악합니다.
2. 각 질문은 자연스럽고 친근하게 물어보세요.
3. 사용자의 답변에 따라 아래 데이터를 JSON 형태로 업데이트합니다.
4. 모든 질문이 끝나면 사용자에게는 간단한 완료 메시지를, 시스템에는 상세한 분석을 제공합니다.

**수집해야 할 데이터 (40개 항목):**

**1-5점 척도 항목들:**
- enjoys_physical_activity: 신체 활동 선호도
- values_social_belonging: 사회적 소속감 중요도  
- likes_adventure: 모험 선호도
- creative_artistic_sense: 창의적/예술적 감성
- competitive_achievement_oriented: 경쟁/성취 지향성
- needs_stress_relief: 스트레스 해소 필요도
- values_learning_growth: 학습/성장 중요도
- needs_recognition: 인정 욕구
- good_concentration: 집중력
- trend_sensitive: 트렌드 민감성
- willing_to_pay_for_hobby: 취미 비용 지불 의향
- likes_long_immersion: 장시간 몰입 선호도
- likes_tangible_results: 가시적 결과 선호도
- likes_digital_tools: 디지털 도구 선호도
- prefers_spontaneous_activity: 즉흥적 활동 선호도

**이진 분류 항목들:**
- sex_encoded: 0(남성), 1(여성)
- I_or_E_encoded: 0(내향), 1(외향)
- N_or_S_encoded: 0(직관), 1(감각) 
- F_or_T_encoded: 0(감정), 1(사고)
- P_or_J_encoded: 0(인식), 1(판단)
- age_encoded: 1(10대), 2(20대), 3(30대), 4(40대), 5(그 이상)

**거주환경 (해당하는 것만 1, 나머지는 0):**
- living_env_1: 대중교통이 편리한 도시 지역
- living_env_2: 자연(산, 바다, 강)에 쉽게 접근 가능
- living_env_3: 대형 쇼핑몰/문화시설이 근처에 있음
- living_env_4: 조용하고 한적한 환경
- living_env_5: 이웃과의 공동체 활동이 활발함
- living_env_6: 다양한 학원/교육 시설이 많음

**직업 (해당하는 것만 1, 나머지는 0):**
- occupation_1: 학생
- occupation_2: 전업 주부/무직
- occupation_3: 직장인(사무직)
- occupation_4: 직장인(현장/기술직)
- occupation_5: 직장인(IT업계)
- occupation_6: 직장인(서비스직)
- occupation_7: 자영업자/프리랜서
- occupation_8: 공무원/공공기관 종사자
- occupation_9: 교사/교수/교육 종사자
- occupation_10: 의료인(간호사, 의사)
- occupation_11: 예술인/창작 활동 종사자
- occupation_12: 임업 주부
- occupation_13: 군인/의무복무자

**응답 형식:**
질문 단계에서는 다음 형식으로 응답하세요:
```
{
  "message": "사용자에게 보여줄 질문이나 대화",
  "user_data": {수집된 데이터 JSON},
  "question_count": 현재_질문_번호,
  "is_complete": false
}
```

모든 질문 완료 시:
```
{
  "message": "이전까지의 질문을 통해 맞춤 취미를 찾았어요! [추천 취미명]",
  "user_data": {완성된_모든_데이터_JSON},
  "summary": "성향 요약 7문장 (데이터베이스 저장용)",
  "recommended_hobby": "추천 취미명",
  "question_count": 15,
  "is_complete": true
}
```

**중요사항:**
- 자연스럽고 친근한 대화체를 사용하세요
- 사용자의 답변을 바탕으로 적절한 수치를 부여하세요
- 15개 질문 안에 모든 40개 항목을 효율적으로 수집하세요
- 최종 완료 시에는 사용자에게는 간단한 완료 메시지와 추천 취미만 보여주고, 성향 요약 7문장은 summary 필드에 별도로 제공하세요
- 성향 요약은 데이터베이스 저장용이므로 구체적이고 정확하게 작성하세요

이제 첫 번째 질문부터 시작하세요!"""

    def initialize_user_data(self) -> Dict:
        """사용자 데이터 초기화"""
        return {
            # 1-5점 척도 항목들
            "enjoys_physical_activity": 0,
            "values_social_belonging": 0,
            "likes_adventure": 0,
            "creative_artistic_sense": 0,
            "competitive_achievement_oriented": 0,
            "needs_stress_relief": 0,
            "values_learning_growth": 0,
            "needs_recognition": 0,
            "good_concentration": 0,
            "trend_sensitive": 0,
            "willing_to_pay_for_hobby": 0,
            "likes_long_immersion": 0,
            "likes_tangible_results": 0,
            "likes_digital_tools": 0,
            "prefers_spontaneous_activity": 0,
            
            # 이진 분류 항목들
            "sex_encoded": 0,
            "I_or_E_encoded": 0,
            "N_or_S_encoded": 0,
            "F_or_T_encoded": 0,
            "P_or_J_encoded": 0,
            "age_encoded": 0,
            
            # 거주환경
            "living_env_1": 0,
            "living_env_2": 0,
            "living_env_3": 0,
            "living_env_4": 0,
            "living_env_5": 0,
            "living_env_6": 0,
            
            # 직업
            "occupation_1": 0,
            "occupation_2": 0,
            "occupation_3": 0,
            "occupation_4": 0,
            "occupation_5": 0,
            "occupation_6": 0,
            "occupation_7": 0,
            "occupation_8": 0,
            "occupation_9": 0,
            "occupation_10": 0,
            "occupation_11": 0,
            "occupation_12": 0,
            "occupation_13": 0
        }

    def parse_ai_response(self, ai_response: str) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
        """AI 응답에서 JSON 데이터, 요약, 추천 취미 파싱"""
        try:
            # AI 응답에서 JSON 부분 추출
            json_str = None
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            elif "{" in ai_response and "}" in ai_response:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                json_str = ai_response[json_start:json_end]
            
            if json_str:
                response_data = json.loads(json_str)
                summary = response_data.get("summary")
                recommended_hobby = response_data.get("recommended_hobby")
                return response_data, summary, recommended_hobby
            
            return None, None, None
            
        except json.JSONDecodeError:
            return None, None, None

    def create_session_data(self) -> list:
        """새로운 세션 데이터 생성"""
        return [
            [],  # history
            None,  # timestamp (외부에서 설정)
            self.initialize_user_data(),  # user_data
            0,  # question_count
            False  # is_profiling_done
        ]

    def get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        return self.system_prompt