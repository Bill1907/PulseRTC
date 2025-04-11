# PulseRTC

WebRTC 서버에 AI Hook을 쉽게 붙일 수 있는 플랫폼입니다.

## 프로젝트 구조

```
├── packages/
│   ├── sfu/              # mediasoup 래핑
│   ├── signaling/        # Fastify + WebSocket
│   ├── ai-hook/          # FastAPI 서버 (Python)
│   ├── client-sdk/       # TypeScript 기반 SDK
│   ├── mobile-sdk/       # Flutter 용
├── examples/
│   ├── web-demo/         # React 기반 예제
│   ├── mobile-demo/      # Flutter 예제
├── docker/
│   └── docker-compose.yml
├── README.md
```

## 주요 기능

- WebRTC SFU(Selective Forwarding Unit) 구현 (mediasoup 기반)
- AI 연동을 위한 Hook 시스템
- 시그널링 서버 (Fastify + WebSocket)
- 클라이언트 SDK (Web, Mobile)

## 개발 환경 설정

본 프로젝트는 pnpm 워크스페이스를 사용합니다.

```bash
# 의존성 설치
pnpm install

# 각 패키지 빌드
pnpm -r build

# 개발 모드 실행
pnpm dev
```

## 패키지 설명

### packages/sfu

mediasoup을 기반으로 한 WebRTC SFU 구현체입니다. WebRTC 미디어 스트림을 라우팅하고 AI Hook과 연동할 수 있는 기능을 제공합니다.

### packages/signaling

Fastify와 WebSocket을 사용한 시그널링 서버입니다. 클라이언트 간의 연결 설정을 조정합니다.

### packages/ai-hook

Python FastAPI 기반의 AI 서비스 연동 서버입니다. 음성 인식, 번역, 감정 분석 등의 AI 기능을 WebRTC 스트림에 연결합니다.

### packages/client-sdk

브라우저 환경에서 사용할 수 있는 TypeScript 기반 SDK 입니다.

### packages/mobile-sdk

Flutter 기반 모바일 환경을 위한 SDK 입니다.

## 라이센스

ISC
