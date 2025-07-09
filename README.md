# 취미추천챗봇 SSAFY 계절학기 AI 프로젝트

> 사용자 정보를 기반으로 개인 맞춤형 취미를 추천하는 플랫폼 어플리케이션   
> [🔗 서비스 체험하러 가기 (Vercel 배포)](https://myhobby-chatbot.vercel.app/)

---

원본 레포지토리 주소: https://github.com/hobby-recommendation-chatbot/backend

### TEAM  
- 김민주 : https://github.com/KimMinjuAstro  
- 김준혁 : https://github.com/peridot0810  
- 박정현 : https://github.com/junghyun0729  
- 오승언 : https://github.com/suee97  
- 하헌석 : https://github.com/rickyhi99  

---

## 프로젝트 개요 & 설계

### 기술 스택

**IDE & LANGUAGE**  
![Visual Studio](https://img.shields.io/badge/Visual%20Studio-3DDC84?style=flat&logo=Visual%20Studio&logoColor=white)  
![JavaScript](https://img.shields.io/badge/javascript-F7DF1E?style=flat-square&logo=javascript&logoColor=white)  
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white)

**BACK**  
![MySQL](https://img.shields.io/badge/mysql-4479A1?style=flat-square&logo=mysql&logoColor=white)

**FRONT**  
![Vue.js](https://img.shields.io/badge/vuedotjs-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)

**진행 기간**  
2025.06.04 ~ 2025.07.04

**목표**  
- 사용자 성향, 성격, 생활환경 등의 정보를 대화 형식으로 수집하여, 개인 맞춤형 취미를 추천하는 인터랙티브 시스템을 구축합니다.  
- 추천된 취미와 유사한 활동들을 벡터 기반 유사도 비교를 통해 제안하고, 각 취미에 대한 상세 정보와 관련 이미지를 함께 제공합니다.

---

## 사용법

1. **홈 화면 접속**  
   [https://myhobby-chatbot.vercel.app/](https://myhobby-chatbot.vercel.app/) 에 접속합니다.

2. **성향 진단 시작**  
   - 챗봇의 질문에 따라 성격, 관심사, 생활 패턴 등의 정보를 대화 형식으로 입력합니다.  
   - 예: "혼자 있는 걸 선호하나요?" → "네 / 아니오"

3. **취미 추천 결과 확인**  
   - 입력한 정보를 기반으로 개인 맞춤 취미가 추천됩니다.  
   - 추천 결과에는 관련 이미지, 준비물, 추가 정보 등이 포함됩니다.

4. **유사 취미 탐색**  
   - 추천된 취미와 유사한 다른 활동들도 함께 확인할 수 있습니다.  
   - 유사도 기반으로 관련 취미가 자동 제안됩니다.

---

## 주요 기능 요약

- 대화 기반 사용자 성향 분석  
- 유사 사용자 기반 1차 추천  
- 유사 취미 벡터 유사도 기반 2차 추천  
- 각 취미의 상세 정보 , 준비물 및 이미지 제공  
- 추가 정보 등 실행 정보 제공  (SerpAPI 기반 실시간 검색 결과 활용)

---

## 배포 링크

👉 [https://myhobby-chatbot.vercel.app/](https://myhobby-chatbot.vercel.app/)

## RAG 파이프라인 구조

![RAG 파이프라인](./docs/서울_3팀_rag파이프라인.png)
