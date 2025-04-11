import { SfuConfig } from "../types";
import * as os from "os";

export const defaultConfig: SfuConfig = {
  worker: {
    logLevel: "warn",
    logTags: ["info", "ice", "dtls", "rtp", "srtp", "rtcp"],
    rtcMinPort: 10000,
    rtcMaxPort: 59999,
    numWorkers: Math.min(4, os.cpus().length),
  },
  router: {
    mediaCodecs: [
      {
        kind: "audio",
        mimeType: "audio/opus",
        clockRate: 48000,
        channels: 2,
      },
      {
        kind: "video",
        mimeType: "video/VP8",
        clockRate: 90000,
        parameters: {
          "x-google-start-bitrate": 1000,
        },
      },
      {
        kind: "video",
        mimeType: "video/VP9",
        clockRate: 90000,
        parameters: {
          "profile-id": 2,
          "x-google-start-bitrate": 1000,
        },
      },
      {
        kind: "video",
        mimeType: "video/h264",
        clockRate: 90000,
        parameters: {
          "packetization-mode": 1,
          "profile-level-id": "4d0032",
          "level-asymmetry-allowed": 1,
          "x-google-start-bitrate": 1000,
        },
      },
    ],
  },
  webRtcTransport: {
    listenIps: [
      {
        ip: "0.0.0.0",
        announcedIp: undefined, // 실제 서버 IP를 여기에 설정
      },
    ],
    initialAvailableOutgoingBitrate: 1000000,
    maxIncomingBitrate: 1500000,
  },
};
