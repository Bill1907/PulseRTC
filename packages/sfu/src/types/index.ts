import * as mediasoup from "mediasoup";

export interface SfuConfig {
  worker: {
    logLevel: mediasoup.types.WorkerLogLevel;
    logTags: mediasoup.types.WorkerLogTag[];
    rtcMinPort: number;
    rtcMaxPort: number;
    numWorkers: number;
  };
  router: {
    mediaCodecs: mediasoup.types.RtpCodecCapability[];
  };
  webRtcTransport: {
    listenIps: mediasoup.types.TransportListenIp[];
    initialAvailableOutgoingBitrate: number;
    maxIncomingBitrate?: number;
  };
}

export interface Room {
  id: string;
  router: mediasoup.types.Router;
  peers: Map<string, Peer>;
}

export interface Peer {
  id: string;
  transports: Map<string, mediasoup.types.WebRtcTransport>;
  producers: Map<string, mediasoup.types.Producer>;
  consumers: Map<string, mediasoup.types.Consumer>;
}

export interface TransportOptions {
  id: string;
  roomId: string;
  peerId: string;
  direction: "send" | "receive";
}

export interface AIHookConfig {
  enabled: boolean;
  endpoint?: string;
  authToken?: string;
}
