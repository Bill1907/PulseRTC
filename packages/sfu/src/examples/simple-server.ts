import { SFU } from "../sfu";
import { config } from "dotenv";
import * as http from "http";
import * as url from "url";

// 환경 변수 로드
config();

// SFU 인스턴스 생성
const sfu = new SFU({
  webRtcTransport: {
    listenIps: [
      {
        ip: "0.0.0.0",
        announcedIp: process.env.ANNOUNCED_IP || undefined, // 공개 IP 주소
      },
    ],
    initialAvailableOutgoingBitrate: 1000000, // 초기 비트레이트 설정
    maxIncomingBitrate: 1500000, // 최대 수신 비트레이트
  },
});

// SFU 이벤트 리스너
sfu.on("producer-score", (data) => {
  console.log(`Producer score updated: ${JSON.stringify(data)}`);
});

sfu.on("consumer-score", (data) => {
  console.log(`Consumer score updated: ${JSON.stringify(data)}`);
});

sfu.on("ai-event", (event) => {
  console.log(`AI Event received: ${JSON.stringify(event)}`);
});

// 간단한 HTTP 서버 생성
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url || "", true);
  const path = parsedUrl.pathname;
  const query = parsedUrl.query;

  // CORS 헤더 설정
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  // OPTIONS 요청 처리
  if (req.method === "OPTIONS") {
    res.writeHead(200);
    res.end();
    return;
  }

  // 기본 라우트
  if (path === "/") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "PulseRTC SFU is running" }));
    return;
  }

  // Router 정보 가져오기
  if (path === "/routers") {
    res.writeHead(200, { "Content-Type": "application/json" });
    // 실제 구현에서는 sfu.getRooms() 등의 메서드를 구현해야 함
    res.end(JSON.stringify({ message: "Not implemented yet" }));
    return;
  }

  // 404 처리
  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not found" }));
});

// 서버 초기화 및 시작
async function start() {
  try {
    // SFU 초기화
    await sfu.init();
    console.log("SFU initialized successfully");

    // AI Hook 설정 (필요 시)
    if (process.env.AI_HOOK_ENABLED === "true") {
      sfu.setAIHookConfig({
        enabled: true,
        endpoint: process.env.AI_HOOK_ENDPOINT,
        authToken: process.env.AI_HOOK_TOKEN,
      });
    }

    // HTTP 서버 시작
    const port = process.env.HTTP_PORT || 3000;
    server.listen(port, () => {
      console.log(`HTTP server listening on port ${port}`);
    });

    // 프로세스 종료 시 정리
    process.on("SIGINT", async () => {
      console.log("Shutting down...");
      await sfu.close();
      server.close();
      process.exit(0);
    });
  } catch (error) {
    console.error("Failed to start the server:", error);
    process.exit(1);
  }
}

// 실행
start();
