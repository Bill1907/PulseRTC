import { SFU } from "./sfu";
import * as mediasoup from "mediasoup";

// mediasoup 모듈 모킹
jest.mock("mediasoup", () => {
  const EventEmitter = require("events");

  // Worker 클래스 모킹
  class MockWorker extends EventEmitter {
    pid = Math.floor(Math.random() * 10000);
    appData = {};

    constructor() {
      super();
    }

    close() {
      this.emit("close");
    }

    async createRouter() {
      return new MockRouter();
    }
  }

  // Router 클래스 모킹
  class MockRouter extends EventEmitter {
    id = `router-${Math.random().toString(36).substring(2, 9)}`;
    appData = {};

    constructor() {
      super();
    }

    close() {
      this.emit("close");
    }

    async createWebRtcTransport() {
      return new MockWebRtcTransport();
    }

    canConsume() {
      return true;
    }
  }

  // WebRtcTransport 클래스 모킹
  class MockWebRtcTransport extends EventEmitter {
    id = `transport-${Math.random().toString(36).substring(2, 9)}`;
    appData = {};

    constructor() {
      super();
    }

    close() {
      this.emit("close");
    }

    async connect() {
      return {};
    }

    async produce() {
      const producer = new MockProducer();
      return producer;
    }

    async consume() {
      const consumer = new MockConsumer();
      return consumer;
    }
  }

  // Producer 클래스 모킹
  class MockProducer extends EventEmitter {
    id = `producer-${Math.random().toString(36).substring(2, 9)}`;
    kind = "audio";
    appData = {};

    constructor() {
      super();
    }

    close() {
      this.emit("close");
    }

    pause() {}

    resume() {}
  }

  // Consumer 클래스 모킹
  class MockConsumer extends EventEmitter {
    id = `consumer-${Math.random().toString(36).substring(2, 9)}`;
    kind = "audio";
    appData = {};
    producerId = `producer-${Math.random().toString(36).substring(2, 9)}`;

    constructor() {
      super();
    }

    close() {
      this.emit("close");
    }

    pause() {}

    resume() {}
  }

  return {
    createWorker: jest.fn().mockImplementation(async () => new MockWorker()),
  };
});

describe("SFU", () => {
  let sfu: SFU;

  beforeEach(async () => {
    sfu = new SFU();
    await sfu.init();
  });

  afterEach(async () => {
    await sfu.close();
  });

  test("SFU 인스턴스 생성", () => {
    expect(sfu).toBeInstanceOf(SFU);
  });

  test("SFU 초기화 성공", () => {
    expect(mediasoup.createWorker).toHaveBeenCalled();
  });

  test("Room 생성 및 관리", async () => {
    const roomId = "test-room";
    const room = await sfu.createRoom(roomId);

    expect(room).toBeDefined();
    expect(room.id).toBe(roomId);

    // 동일한 ID로 Room 생성 시 기존 Room 반환 확인
    const existingRoom = await sfu.createRoom(roomId);
    expect(existingRoom).toBe(room);

    // Room 닫기
    const result = sfu.closeRoom(roomId);
    expect(result).toBe(true);

    // 존재하지 않는 Room 닫기
    const invalidResult = sfu.closeRoom("non-existent-room");
    expect(invalidResult).toBe(false);
  });

  test("Peer 생성 및 관리", async () => {
    const roomId = "test-room";
    const peerId = "test-peer";

    await sfu.createRoom(roomId);
    const peer = sfu.createPeer(roomId, peerId);

    expect(peer).toBeDefined();
    expect(peer?.id).toBe(peerId);

    // 동일한 ID로 Peer 생성 시 기존 Peer 반환 확인
    const existingPeer = sfu.createPeer(roomId, peerId);
    expect(existingPeer).toBe(peer);

    // Peer 닫기
    const result = sfu.closePeer(roomId, peerId);
    expect(result).toBe(true);

    // 존재하지 않는 Peer 닫기
    const invalidResult = sfu.closePeer(roomId, "non-existent-peer");
    expect(invalidResult).toBe(false);
  });

  test("Transport 생성", async () => {
    const roomId = "test-room";
    const peerId = "test-peer";
    const transportId = "test-transport";

    await sfu.createRoom(roomId);
    sfu.createPeer(roomId, peerId);

    const transport = await sfu.createWebRtcTransport({
      id: transportId,
      roomId,
      peerId,
      direction: "send",
    });

    expect(transport).toBeDefined();
    expect(transport?.id).toBeDefined();
  });

  test("존재하지 않는 Room에 Transport 생성 시도", async () => {
    const transport = await sfu.createWebRtcTransport({
      id: "test-transport",
      roomId: "non-existent-room",
      peerId: "test-peer",
      direction: "send",
    });

    expect(transport).toBeNull();
  });

  test("AI Hook 설정", () => {
    sfu.setAIHookConfig({
      enabled: true,
      endpoint: "http://localhost:3000/ai",
    });
    // 이벤트 테스트를 위해 스파이 생성
    const spy = jest.spyOn(sfu, "emit");

    // Room 및 Peer 생성
    const roomId = "test-room";
    const peerId = "test-peer";
    sfu.createRoom(roomId).then(() => {
      sfu.createPeer(roomId, peerId);
      sfu
        .createWebRtcTransport({
          id: "test-transport",
          roomId,
          peerId,
          direction: "send",
        })
        .then((transport) => {
          if (transport) {
            sfu
              .createProducer(roomId, peerId, "test-transport", "audio", {
                codecs: [],
                headerExtensions: [],
                encodings: [],
                rtcp: {},
              })
              .then(() => {
                expect(spy).toHaveBeenCalledWith(
                  "ai-hook-producer",
                  expect.any(Object)
                );
              });
          }
        });
    });
  });
});
