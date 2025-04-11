"""스트림 데이터 처리 API 라우터."""

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.deps import (
    get_emotion_analysis_service,
    get_speech_recognition_service,
    get_sfu_client,
    get_translation_service,
)
from app.core.config import settings
from app.schemas import (
    AIHookEvent,
    AIHookEventType,
    EmotionResult,
    MediaKind,
    MediaStreamRequest,
    TranscriptionResult,
    TranslationResult,
)
from app.services.asr import SpeechRecognitionService
from app.services.emotion import EmotionAnalysisService
from app.services.sfu_client import SfuClient
from app.services.translation import TranslationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/stream",
    status_code=status.HTTP_202_ACCEPTED,
    summary="미디어 스트림 처리 요청",
    description="미디어 스트림을 처리하도록 요청합니다.",
)
async def process_stream(
    request: MediaStreamRequest,
    asr_service: SpeechRecognitionService = Depends(get_speech_recognition_service),
    translation_service: TranslationService = Depends(get_translation_service),
    emotion_service: EmotionAnalysisService = Depends(get_emotion_analysis_service),
    sfu_client: SfuClient = Depends(get_sfu_client),
) -> Dict[str, Any]:
    """미디어 스트림 처리 요청 API.
    
    Args:
        request: 미디어 스트림 요청 정보
        asr_service: 음성 인식 서비스
        translation_service: 번역 서비스
        emotion_service: 감정 분석 서비스
        sfu_client: SFU 클라이언트
        
    Returns:
        처리 결과
    """
    if request.kind != MediaKind.AUDIO:
        # 현재는 오디오만 지원
        return {"status": "ignored", "reason": "only audio streams are supported"}
    
    # SFU에 연결 및 스트림 구독 요청
    try:
        await sfu_client.connect()
        await sfu_client.subscribe_to_stream(
            request.roomId, request.peerId, request.producerId
        )
        
        return {
            "status": "accepted", 
            "stream_id": request.producerId,
            "services": {
                "asr": settings.ENABLE_SPEECH_RECOGNITION,
                "translation": settings.ENABLE_TRANSLATION,
                "emotion": settings.ENABLE_EMOTION_ANALYSIS,
            }
        }
    except Exception as e:
        logger.exception("Failed to process stream request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    asr_service: SpeechRecognitionService = Depends(get_speech_recognition_service),
    translation_service: TranslationService = Depends(get_translation_service),
    emotion_service: EmotionAnalysisService = Depends(get_emotion_analysis_service),
    sfu_client: SfuClient = Depends(get_sfu_client),
) -> None:
    """WebSocket 연결 엔드포인트.
    
    Args:
        websocket: WebSocket 연결
        asr_service: 음성 인식 서비스
        translation_service: 번역 서비스
        emotion_service: 감정 분석 서비스
        sfu_client: SFU 클라이언트
    """
    # WebSocket 연결 수락
    await websocket.accept()
    
    # 클라이언트 정보 추출 (쿼리 파라미터)
    query_params = websocket.query_params
    client_id = query_params.get("clientId", "unknown")
    
    # 이벤트 구독 및 전송 루프
    try:
        # SFU 클라이언트의 이벤트 구독
        sfu_client.subscribe_to_events(on_asr_result, on_translation_result, on_emotion_result)
        
        # 하트비트 타이머
        last_ping = asyncio.get_event_loop().time()
        
        while True:
            # 메시지 수신 또는 타임아웃
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=settings.WS_HEARTBEAT_INTERVAL
                )
                # 클라이언트로부터 메시지 수신
                message = data.strip()
                if message == "ping":
                    await websocket.send_text("pong")
                    last_ping = asyncio.get_event_loop().time()
            except asyncio.TimeoutError:
                # 하트비트 체크
                if (asyncio.get_event_loop().time() - last_ping) > settings.WS_HEARTBEAT_INTERVAL * 2:
                    logger.warning(f"Client {client_id} heartbeat timeout")
                    break
                
                # 하트비트 메시지 전송
                await websocket.send_text("ping")
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.exception(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason=str(e))
    
    finally:
        # 정리
        sfu_client.unsubscribe_from_events()


# 콜백 함수들
async def on_asr_result(
    result: TranscriptionResult, 
    room_id: str, 
    peer_id: str, 
    producer_id: str,
    websocket: WebSocket
) -> None:
    """ASR 결과 콜백.
    
    Args:
        result: 음성 인식 결과
        room_id: 방 ID
        peer_id: 피어 ID
        producer_id: 프로듀서 ID
        websocket: WebSocket 연결
    """
    event = AIHookEvent(
        type=AIHookEventType.TRANSCRIPTION,
        roomId=room_id,
        peerId=peer_id,
        producerId=producer_id,
        data=result.dict()
    )
    await websocket.send_json(event.dict())


async def on_translation_result(
    result: TranslationResult, 
    room_id: str, 
    peer_id: str, 
    producer_id: str,
    websocket: WebSocket
) -> None:
    """번역 결과 콜백.
    
    Args:
        result: 번역 결과
        room_id: 방 ID
        peer_id: 피어 ID
        producer_id: 프로듀서 ID
        websocket: WebSocket 연결
    """
    event = AIHookEvent(
        type=AIHookEventType.TRANSLATION,
        roomId=room_id,
        peerId=peer_id,
        producerId=producer_id,
        data=result.dict()
    )
    await websocket.send_json(event.dict())


async def on_emotion_result(
    result: EmotionResult, 
    room_id: str, 
    peer_id: str, 
    producer_id: str,
    websocket: WebSocket
) -> None:
    """감정 분석 결과 콜백.
    
    Args:
        result: 감정 분석 결과
        room_id: 방 ID
        peer_id: 피어 ID
        producer_id: 프로듀서 ID
        websocket: WebSocket 연결
    """
    event = AIHookEvent(
        type=AIHookEventType.EMOTION,
        roomId=room_id,
        peerId=peer_id,
        producerId=producer_id,
        data=result.dict()
    )
    await websocket.send_json(event.dict()) 