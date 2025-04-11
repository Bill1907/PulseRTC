import axios from "axios";
import { EventEmitter } from "events";
import { AIHookConfig } from "../types";

export class AIHookConnector extends EventEmitter {
  private config: AIHookConfig = { enabled: false };
  private connectionStatus: "connected" | "disconnected" | "failed" =
    "disconnected";

  constructor(config?: AIHookConfig) {
    super();
    if (config) {
      this.config = config;
    }
  }

  /**
   * AI Hook 설정
   */
  public setConfig(config: AIHookConfig): void {
    this.config = config;
    if (config.enabled && config.endpoint) {
      this.testConnection();
    }
  }

  /**
   * AI 서비스와의 연결 테스트
   */
  private async testConnection(): Promise<boolean> {
    if (!this.config.enabled || !this.config.endpoint) {
      this.connectionStatus = "disconnected";
      return false;
    }

    try {
      const response = await axios.get(`${this.config.endpoint}/health`, {
        headers: this.config.authToken
          ? {
              Authorization: `Bearer ${this.config.authToken}`,
            }
          : undefined,
        timeout: 5000,
      });

      if (response.status === 200) {
        this.connectionStatus = "connected";
        return true;
      }

      this.connectionStatus = "failed";
      return false;
    } catch (error) {
      console.error("AI Hook 연결 테스트 실패:", error);
      this.connectionStatus = "failed";
      return false;
    }
  }

  /**
   * 미디어 스트림을 AI 서비스로 전송
   */
  public async sendMediaStream(data: {
    roomId: string;
    peerId: string;
    producerId: string;
    kind: "audio" | "video";
    metadata?: Record<string, any>;
  }): Promise<void> {
    if (!this.config.enabled || !this.config.endpoint) {
      return;
    }

    try {
      await axios.post(`${this.config.endpoint}/stream`, data, {
        headers: this.config.authToken
          ? {
              Authorization: `Bearer ${this.config.authToken}`,
            }
          : undefined,
      });

      this.emit("stream-sent", {
        success: true,
        ...data,
      });
    } catch (error) {
      console.error("AI Hook 스트림 전송 실패:", error);
      this.emit("stream-sent", {
        success: false,
        error,
        ...data,
      });
    }
  }

  /**
   * AI 서비스로부터 이벤트 수신 (Webhook 처리용)
   */
  public handleAIEvent(event: any): void {
    this.emit("ai-event", event);
  }

  /**
   * 현재 연결 상태 가져오기
   */
  public getConnectionStatus(): "connected" | "disconnected" | "failed" {
    return this.connectionStatus;
  }
}
