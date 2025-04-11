import { AIHookConnector } from "./index";
import axios from "axios";

// axios 모듈 모킹
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("AIHookConnector", () => {
  let aiHook: AIHookConnector;

  beforeEach(() => {
    // 테스트 전 axios 모킹 초기화
    jest.clearAllMocks();
    aiHook = new AIHookConnector();
  });

  test("기본 설정으로 생성", () => {
    expect(aiHook).toBeInstanceOf(AIHookConnector);
    expect(aiHook.getConnectionStatus()).toBe("disconnected");
  });

  test("AI Hook 설정 업데이트", () => {
    // axios 응답 모킹
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: { status: "healthy" },
    });

    aiHook.setConfig({
      enabled: true,
      endpoint: "http://localhost:3000/ai",
      authToken: "test-token",
    });

    expect(mockedAxios.get).toHaveBeenCalledWith(
      "http://localhost:3000/ai/health",
      expect.objectContaining({
        headers: { Authorization: "Bearer test-token" },
        timeout: 5000,
      })
    );
  });

  test("미디어 스트림 전송", async () => {
    // axios 응답 모킹
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { success: true },
    });

    // 이벤트 스파이 설정
    const eventSpy = jest.fn();
    aiHook.on("stream-sent", eventSpy);

    // AI Hook 설정
    aiHook.setConfig({
      enabled: true,
      endpoint: "http://localhost:3000/ai",
    });

    // 미디어 스트림 데이터
    const streamData = {
      roomId: "test-room",
      peerId: "test-peer",
      producerId: "test-producer",
      kind: "audio" as const,
      metadata: { language: "ko" },
    };

    // 스트림 전송
    await aiHook.sendMediaStream(streamData);

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "http://localhost:3000/ai/stream",
      streamData,
      expect.any(Object)
    );

    // 이벤트 발생 확인
    expect(eventSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        roomId: "test-room",
        peerId: "test-peer",
        producerId: "test-producer",
      })
    );
  });

  test("AI Hook이 비활성화된 경우 스트림 전송하지 않음", async () => {
    // AI Hook 비활성화
    aiHook.setConfig({ enabled: false });

    // 미디어 스트림 데이터
    const streamData = {
      roomId: "test-room",
      peerId: "test-peer",
      producerId: "test-producer",
      kind: "audio" as const,
    };

    // 스트림 전송
    await aiHook.sendMediaStream(streamData);

    // axios.post가 호출되지 않아야 함
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  test("AI 이벤트 처리", () => {
    // 이벤트 스파이 설정
    const eventSpy = jest.fn();
    aiHook.on("ai-event", eventSpy);

    // AI 이벤트 데이터
    const aiEvent = {
      type: "transcription",
      roomId: "test-room",
      peerId: "test-peer",
      text: "안녕하세요",
      confidence: 0.95,
    };

    // 이벤트 처리
    aiHook.handleAIEvent(aiEvent);

    // 이벤트 발생 확인
    expect(eventSpy).toHaveBeenCalledWith(aiEvent);
  });
});
