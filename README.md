# 🎧 PulseRTC

> 다양한 음성 기반 AI 모델(GPT-4o, Claude Sonnet, Gemini 등)을 자유로 선택하여 실시간 대화를 진행하는 WebRTC 기반 오픈 플랫폼

---

## 💡 프로젝트 개요

이 플랫폼은 사용자가 선택한 AI 모델과 음성 기반으로 실시간 대화를 나누어 쓰는 구조로 되어 있습니다.  
WebRTC를 통해 실시간 음성 데이터를 주고받고, AI 모델은 STT → LLM → TTS의 화름으로 응답을 생성합니다.

### 주요 특징

- ✅ 다양한 AI 모델 연동 (GPT-4o, Claude, Gemini 등)
- 🎧 실시간 WebRTC 기반 음성 스트림링
- 🧠 STT → LLM → TTS 화름 자동 연결
- 🚀 Docker Compose로 간편한 로컬 및 클라우드 실행
- 🛠️ 완전 모듈화된 구조 (Signaling / Media Gateway / Model Router)

---

## 📦 시스템 구성

```
[Client SDK]
    ↓
[Signaling Server] ← REST API + WebSocket
    ↓
[WebRTC Media Gateway]
    ↓
[Model Routing Layer] → STT → GPT/Claude/Gemini → TTS
```

---

## 🛠️ 개발 스텍

| 구성 요소     | 기술 스텍                                            |
| ------------- | ---------------------------------------------------- |
| Client SDK    | TypeScript (Flutter / WebRTC)                        |
| Signaling     | Node.js + Express / WebSocket                        |
| Media Gateway | mediasoup or ion-sfu (Node or Go)                    |
| Model Router  | TypeScript + Whisper API + OpenAI/Claude/Gemini APIs |

---

## 🔪 로컬 실행 방법

```bash
git clone https://github.com/yourname/webrtc-ai-platform.git
cd webrtc-ai-platform
docker-compose up --build
```

- 브라우저에서 http://localhost:3000 접속
- SDK를 통해 세션 생성 후 WebRTC 연결
- AI 응답 음성 수습 확인

---

## 📁 디렉토리 구성

```
/client-sdk         # Web or Flutter SDK
/signaling-server   # REST + WS 세션 관리 서버
/media-gateway      # WebRTC audio stream 핸들링
/model-router       # STT → LLM → TTS 라우팅 처리
/docker-compose.yml # 전체 실행 스크립트
```

---

## 📌 협정 계획

- [ ] Whisper 대신 다른 STT 옵션 추가 (Google, Azure 등)
- [ ] LLM 라우팅 구조 플랫그인화
- [ ] 실시간 응답 중단 처리 (interrupt)
- [ ] 텍스트 로그 저장 기능

---
