import * as mediasoup from "mediasoup";
import { EventEmitter } from "events";
import { SfuConfig, Room, Peer, TransportOptions, AIHookConfig } from "./types";
import { defaultConfig } from "./config/default";
import { AIHookConnector } from "./ai-hook";

export class SFU extends EventEmitter {
  private config: SfuConfig;
  private workers: mediasoup.types.Worker[] = [];
  private nextWorkerIndex = 0;
  private rooms: Map<string, Room> = new Map();
  private aiHookConfig: AIHookConfig = { enabled: false };
  private aiHookConnector: AIHookConnector;

  constructor(config?: Partial<SfuConfig>) {
    super();
    this.config = { ...defaultConfig, ...config };
    this.aiHookConnector = new AIHookConnector();

    // AI Hook 이벤트 연결
    this.aiHookConnector.on("ai-event", (event) => {
      this.emit("ai-event", event);
    });

    this.aiHookConnector.on("stream-sent", (result) => {
      this.emit("ai-stream-sent", result);
    });
  }

  /**
   * SFU 초기화 - worker 생성
   */
  public async init(): Promise<void> {
    const { numWorkers, ...workerSettings } = this.config.worker;

    for (let i = 0; i < numWorkers; i++) {
      const worker = await mediasoup.createWorker(workerSettings);

      worker.on("died", () => {
        console.error(`Worker ${worker.pid} died, exiting in 2 seconds...`);
        setTimeout(() => process.exit(1), 2000);
      });

      this.workers.push(worker);
    }

    console.log(`Created ${numWorkers} mediasoup workers`);
  }

  /**
   * 다음 사용 가능한 Worker 가져오기 (라운드 로빈 방식)
   */
  private getNextWorker(): mediasoup.types.Worker {
    const worker = this.workers[this.nextWorkerIndex];
    this.nextWorkerIndex = (this.nextWorkerIndex + 1) % this.workers.length;
    return worker;
  }

  /**
   * 새로운 Room 생성
   */
  public async createRoom(roomId: string): Promise<Room> {
    if (this.rooms.has(roomId)) {
      return this.rooms.get(roomId)!;
    }

    const worker = this.getNextWorker();
    const router = await worker.createRouter({
      mediaCodecs: this.config.router.mediaCodecs,
    });

    const room: Room = {
      id: roomId,
      router,
      peers: new Map(),
    };

    this.rooms.set(roomId, room);
    console.log(`Created room with ID: ${roomId}`);

    return room;
  }

  /**
   * Room 제거
   */
  public closeRoom(roomId: string): boolean {
    const room = this.rooms.get(roomId);

    if (!room) {
      return false;
    }

    // Close all peers in the room
    for (const peer of room.peers.values()) {
      this.closePeer(roomId, peer.id);
    }

    // Close router
    room.router.close();
    this.rooms.delete(roomId);

    console.log(`Closed room with ID: ${roomId}`);
    return true;
  }

  /**
   * 새로운 Peer 생성
   */
  public createPeer(roomId: string, peerId: string): Peer | null {
    const room = this.rooms.get(roomId);

    if (!room) {
      console.error(`Room with ID ${roomId} not found`);
      return null;
    }

    if (room.peers.has(peerId)) {
      return room.peers.get(peerId)!;
    }

    const peer: Peer = {
      id: peerId,
      transports: new Map(),
      producers: new Map(),
      consumers: new Map(),
    };

    room.peers.set(peerId, peer);
    console.log(`Created peer ${peerId} in room ${roomId}`);

    return peer;
  }

  /**
   * Peer 제거
   */
  public closePeer(roomId: string, peerId: string): boolean {
    const room = this.rooms.get(roomId);

    if (!room) {
      return false;
    }

    const peer = room.peers.get(peerId);

    if (!peer) {
      return false;
    }

    // Close all transports
    for (const transport of peer.transports.values()) {
      transport.close();
    }

    room.peers.delete(peerId);
    console.log(`Closed peer ${peerId} in room ${roomId}`);

    return true;
  }

  /**
   * WebRTC 트랜스포트 생성
   */
  public async createWebRtcTransport(
    options: TransportOptions
  ): Promise<mediasoup.types.WebRtcTransport | null> {
    const { roomId, peerId, id: transportId, direction } = options;

    const room = this.rooms.get(roomId);
    if (!room) {
      console.error(`Room with ID ${roomId} not found`);
      return null;
    }

    const peer = room.peers.get(peerId);
    if (!peer) {
      console.error(`Peer with ID ${peerId} not found in room ${roomId}`);
      return null;
    }

    const transport = await room.router.createWebRtcTransport({
      ...this.config.webRtcTransport,
      enableUdp: true,
      enableTcp: true,
      preferUdp: true,
      appData: { peerId, roomId, transportId, direction },
    });

    // 연결 에러 핸들링
    transport.on("dtlsstatechange", (dtlsState) => {
      if (dtlsState === "failed" || dtlsState === "closed") {
        console.error(
          `WebRtcTransport dtls failed or closed [peerId:${peerId}, transportId:${transportId}]`
        );
      }
    });

    peer.transports.set(transportId, transport);

    return transport;
  }

  /**
   * Producer 생성 (미디어 스트림 전송)
   */
  public async createProducer(
    roomId: string,
    peerId: string,
    transportId: string,
    kind: mediasoup.types.MediaKind,
    rtpParameters: mediasoup.types.RtpParameters,
    appData?: Record<string, unknown>
  ): Promise<mediasoup.types.Producer | null> {
    const room = this.rooms.get(roomId);
    if (!room) return null;

    const peer = room.peers.get(peerId);
    if (!peer) return null;

    const transport = peer.transports.get(transportId);
    if (!transport) return null;

    const producer = await transport.produce({
      kind,
      rtpParameters,
      appData: { ...appData, peerId, roomId },
    });

    producer.on("transportclose", () => {
      console.log(`Producer transport closed [producerId:${producer.id}]`);
      peer.producers.delete(producer.id);
    });

    producer.on("score", (score) => {
      // RTP 품질 모니터링
      this.emit("producer-score", {
        peerId,
        roomId,
        producerId: producer.id,
        score,
      });
    });

    peer.producers.set(producer.id, producer);

    // AI Hook이 활성화된 경우 미디어 스트림 전송
    if (this.aiHookConfig.enabled) {
      this.emit("ai-hook-producer", {
        roomId,
        peerId,
        producerId: producer.id,
        kind,
      });

      // AI Hook으로 스트림 데이터 전송
      this.aiHookConnector.sendMediaStream({
        roomId,
        peerId,
        producerId: producer.id,
        kind: kind as "audio" | "video",
        metadata: appData,
      });
    }

    return producer;
  }

  /**
   * Consumer 생성 (미디어 스트림 수신)
   */
  public async createConsumer(
    roomId: string,
    consumerPeerId: string,
    producerPeerId: string,
    producerId: string,
    transportId: string,
    rtpCapabilities: mediasoup.types.RtpCapabilities
  ): Promise<mediasoup.types.Consumer | null> {
    const room = this.rooms.get(roomId);
    if (!room) return null;

    const consumerPeer = room.peers.get(consumerPeerId);
    if (!consumerPeer) return null;

    const transport = consumerPeer.transports.get(transportId);
    if (!transport) return null;

    // Producer가 존재하는지 확인
    const producerPeer = room.peers.get(producerPeerId);
    if (!producerPeer) return null;

    const producer = producerPeer.producers.get(producerId);
    if (!producer) return null;

    // Router가 Consumer의 RTP 기능 지원 여부 확인
    if (
      !room.router.canConsume({
        producerId: producer.id,
        rtpCapabilities,
      })
    ) {
      console.error(
        `Router cannot consume [peerId:${consumerPeerId}, producerId:${producerId}]`
      );
      return null;
    }

    const consumer = await transport.consume({
      producerId: producer.id,
      rtpCapabilities,
      paused: true, // 처음에는 일시 정지 상태
      appData: {
        peerId: consumerPeerId,
        producerPeerId,
        roomId,
      },
    });

    consumer.on("transportclose", () => {
      console.log(`Consumer transport closed [consumerId:${consumer.id}]`);
      consumerPeer.consumers.delete(consumer.id);
    });

    consumer.on("producerclose", () => {
      console.log(`Consumer producer closed [consumerId:${consumer.id}]`);
      consumerPeer.consumers.delete(consumer.id);
      this.emit("consumer-producer-closed", {
        roomId,
        peerId: consumerPeerId,
        consumerId: consumer.id,
      });
    });

    consumer.on("score", (score) => {
      // 소비자 RTP 품질 모니터링
      this.emit("consumer-score", {
        peerId: consumerPeerId,
        roomId,
        consumerId: consumer.id,
        score,
      });
    });

    consumerPeer.consumers.set(consumer.id, consumer);

    return consumer;
  }

  /**
   * AI Hook 설정
   */
  public setAIHookConfig(config: AIHookConfig): void {
    this.aiHookConfig = config;
    this.aiHookConnector.setConfig(config);
    console.log(`AI Hook ${config.enabled ? "enabled" : "disabled"}`);
  }

  /**
   * AI 이벤트 처리
   */
  public handleAIEvent(event: any): void {
    this.aiHookConnector.handleAIEvent(event);
  }

  /**
   * AI Hook 연결 상태 확인
   */
  public getAIHookStatus(): "connected" | "disconnected" | "failed" {
    return this.aiHookConnector.getConnectionStatus();
  }

  /**
   * SFU 정리 (종료 시)
   */
  public async close(): Promise<void> {
    // 모든 room 종료
    for (const roomId of this.rooms.keys()) {
      this.closeRoom(roomId);
    }

    // 모든 worker 종료
    for (const worker of this.workers) {
      worker.close();
    }

    this.workers = [];
    this.rooms.clear();
    console.log("SFU closed");
  }
}
