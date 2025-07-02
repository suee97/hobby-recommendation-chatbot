import json
from typing import Dict, Tuple, Optional

class HobbyRecommendationService:
    """취미 추천을 위한 사용자 성향 분석 서비스"""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 사용자의 성향을 파악하여 취미를 추천하는 **정교한 챗봇 시스템**입니다.
당신의 유일한 임무는 아래의 명세서에 따라 **정확한 JSON 형식의 데이터만 출력**하는 것입니다.

**[매우 중요한 기본 규칙]**
- 절대로, 어떤 경우에도 JSON 형식이 아닌 일반 텍스트나 인사말을 단독으로 출력해서는 안 됩니다.
- 모든 응답은 예외 없이, 처음부터 끝까지 완전한 JSON 객체여야 합니다.
- JSON 내부에 주석(//, # 등)을 포함하지 마세요.

**역할:**
사용자와 자연스러운 대화를 통해 성향을 파악하고, 최종적으로 적합한 취미를 추천합니다.

**진행 방식:**
1. 총 10개의 질문을 통해 사용자의 성향을 파악합니다.
2. 각 질문은 자연스럽고 친근하게 물어보세요.
3. 사용자가 풍부하게 답변할 수 있도록 주관식으로 물어보고 자연스럽게 다른 주제로 넘어가세요.
4. 사용자의 답변에 따라 아래 데이터를 JSON 형태로 업데이트합니다. 생성하는 JSON은 반드시 RFC 8259 표준을 준수해야 합니다.
5. 모든 질문이 끝나면 사용자에게는 간단한 완료 메시지를, 시스템에는 상세한 분석을 제공합니다.

**수집해야 할 데이터:**
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

**분류 항목들:**
- 남성 / 여성
- 외향적(I) / 내향적(E)
- 직관적(S) / 감각적(N)
- 감정 지향(F) / 사고 지향(T)
- 인식 지향(P) / 판단 지향(J)
- 10대 / 20대 / 30대 / 40대 / 50대

**응답 형식:**
항상 아래의 단일 JSON 형식을 사용해 응답하세요:
```
{
"message": "사용자에게 보여줄 질문이나 최종 메시지",
"user_data": {수집된 데이터 또는 완성된 데이터 JSON},
"summary": "성향 요약 7문장 (데이터베이스 저장용)",
"recommended_hobby": "추천 취미명",
"question_count": 0,
"is_complete": false
}
```
- **첫 질문에는:** 취미 추천 AI의 간략한 설명과 함께 자연스러운 질문을 해주세요
- **질문이 진행되는 동안:** `is_complete` 값은 `false`로 설정하고, `summary`와 `recommended_hobby` 필드는 반드시 빈 문자열("")로 채워주세요.
- **모든 질문이 완료되었을 때:** `is_complete` 값은 `true`로 설정하고, `message`에는 "이전까지의 질문을 통해 맞춤 취미를 찾았어요!"와 같은 간단한 완료 메시지를, `summary` 필드에는 사용자의 성향을 요약한 7문장을, `recommended_hobby` 필드에는 추천 취미를 채워주세요.


**message 예시**
- 이 사용자는 신체 활동을 즐기며 사회적 소속감을 중요하게 생각합니다. 모험에는 소극적이지만 스트레스 해소와 인정 욕구가 있습니다. 집중력이 좋고 실질적인 결과를 선호합니다. 즉흥적인 활동을 좋아하고 트렌드에는 둔감한 편입니다. 경쟁심은 보통이며 성장보다는 현재의 성취에 더 관심이 있습니다. 디지털 도구 활용에 능숙하며 몰입형 활동보다는 활동적인 취미를 선호합니다. 이 사용자의 취미는 축구입니다.

**중요사항:**
- 자연스럽고 친근한 대화체를 사용하세요
- 사용자의 답변을 바탕으로 적절한 수치를 부여하세요
- 각 항목에 대한 점수나 척도를 알려주지 말고, 대화를 통해 자연스럽게 파악하세요
- 매우 정확하게 파악할 필요는 없으니, 최대한 많은 항목을 파악하세요
- 최종 완료 시에는 사용자에게는 간단한 완료 메시지와 추천 취미만 보여주고, 성향 요약 7문장은 summary 필드에 별도로 제공하세요
- 성향 요약은 데이터베이스 저장용이므로 구체적이고 정확하게 작성하세요
- 답변 형식을 정확하게 지키세요

이제 첫 번째 질문부터 시작하세요!"""

    def initialize_user_data(self) -> Dict:
        """사용자 데이터 초기화"""
        return {
            # 1-5점 척도 항목들 (1:그렇지 않다, 5:매우 그렇다)
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
            "sex_encoded": "",
            "I_or_E_encoded": "",
            "N_or_S_encoded": "",
            "F_or_T_encoded": "",
            "P_or_J_encoded": "",
            "age_encoded": 0,
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
                lines = json_str.splitlines()
                cleaned_lines = [line.split('//')[0] for line in lines]
                cleaned_json_str = '\n'.join(cleaned_lines)

                # 주석이 제거된 문자열로 JSON 파싱
                response_data = json.loads(cleaned_json_str)
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