# @pulsertc/sfu

PulseRTC의 SFU(Selective Forwarding Unit) 구현 패키지입니다. 이 패키지는 [mediasoup](https://mediasoup.org/)을 기반으로 하여 WebRTC 미디어 스트림을 효율적으로 라우팅하고 AI 기능을 연결할 수 있는 기능을 제공합니다.

## 설치

```bash
pnpm add @pulsertc/sfu
```

## 주요 기능

- WebRTC 미디어 스트림을 위한 SFU 구현
- 미디어 라우팅 및 관리
- Room 및 Peer 기반 세션 관리
- Producer/Consumer 모델 지원
- AI Hook 연동 지원

## 사용법

### 기본 설정

```typescript
import { SFU } from "@pulsertc/sfu";

// SFU 인스턴스 생성
const sfu = new SFU({
  worker: {
    // 커스텀 worker 설정
    numWorkers: 2, // CPU 코어 수에 맞게 조정
  },
  webRtcTransport: {
    listenIps: [
      {
        ip: "0.0.0.0",
        announcedIp: "공인 IP 주소", // 외부에서 접근할 IP 주소
      },
    ],
  },
});

// SFU 초기화
await sfu.init();
```

### Room 및 Peer 관리

```typescript
// Room 생성
const room = await sfu.createRoom("room-id");

// Peer 생성
const peer = sfu.createPeer("room-id", "peer-id");

// WebRTC Transport 생성
const sendTransport = await sfu.createWebRtcTransport({
  id: "send-transport-id",
  roomId: "room-id",
  peerId: "peer-id",
  direction: "send",
});

const receiveTransport = await sfu.createWebRtcTransport({
  id: "receive-transport-id",
  roomId: "room-id",
  peerId: "peer-id",
  direction: "receive",
});
```

### Producer 및 Consumer 생성

```typescript
// Producer 생성 (미디어 전송)
const producer = await sfu.createProducer(
  "room-id",
  "peer-id",
  "send-transport-id",
  "audio", // 또는 'video'
  rtpParameters // 클라이언트 SDK로부터 수신한 RTP 파라미터
);

// Consumer 생성 (미디어 수신)
const consumer = await sfu.createConsumer(
  "room-id",
  "consumer-peer-id",
  "producer-peer-id",
  "producer-id",
  "receive-transport-id",
  rtpCapabilities // 클라이언트 SDK로부터 수신한 RTP 기능
);
```

### AI Hook 활성화

```typescript
// AI Hook 설정
sfu.setAIHookConfig({
  enabled: true,
  endpoint: "https://ai-service.example.com/hook",
  authToken: "your-auth-token",
});

// AI 이벤트 수신
sfu.on("ai-hook-producer", ({ roomId, peerId, producerId, kind }) => {
  // AI 서비스에 연결하는 로직
  console.log(`AI Hook for producer ${producerId} in room ${roomId}`);
});
```

## 테스트

```bash
pnpm test
```

## 라이센스

ISC
