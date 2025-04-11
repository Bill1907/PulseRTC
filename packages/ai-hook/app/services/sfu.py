"""SFU 클라이언트 서비스."""

import asyncio
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas import MediaStreamRequest

logger = logging.getLogger(__name__)


class SfuServiceEvent(BaseModel):
    """SFU 서비스 이벤트."""
    
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    room_id: str
    peer_id: str
    producer_id: Optional[str] = None


class SfuClient:
    """SFU 클라이언트."""
    
    def __init__(self) -> None:
        """초기화."""
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self.client_id = f"ai-hook-{uuid.uuid4()}"
        
        # 구독 중인 스트림들
        self.subscribed_streams: Set[Tuple[str, str, str]] = set()  # (room_id, peer_id, producer_id)
        
        # 이벤트 콜백
        self.event_callbacks: List[Callable[[SfuServiceEvent], Any]] = []
        
        # 재연결 관련
        self.reconnect_task: Optional[asyncio.Task] = None
        self.reconnect_interval = 2.0  # 초기 재연결 간격 (초)
        self.max_reconnect_interval = 30.0  # 최대 재연결 간격 (초)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # 핑/퐁 핸들러
        self.last_pong_time: float = 0.0
        self.ping_interval: float = 30.0  # 30초마다 핑
        self.ping_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """SFU 서버에 연결.
        
        Returns:
            연결 성공 여부
        """
        if self.is_connected:
            return True
        
        logger.info(f"Connecting to SFU server at {settings.SFU_WS_URL}")
        
        try:
            self.session = aiohttp.ClientSession()
            self.websocket = await self.session.ws_connect(
                settings.SFU_WS_URL,
                heartbeat=30.0,
                timeout=10.0,
            )
            
            # 연결 성공 후 인증
            auth_message = {
                "type": "auth",
                "data": {
                    "client_id": self.client_id,
                    "client_type": "ai-service",
                    "token": settings.SFU_AUTH_TOKEN,
                }
            }
            await self.websocket.send_json(auth_message)
            
            # 인증 응답 대기
            auth_response = await self.websocket.receive_json(timeout=5.0)
            
            if auth_response.get("type") != "auth-success":
                logger.error(f"SFU authentication failed: {auth_response}")
                await self.disconnect()
                return False
            
            logger.info("Connected to SFU server successfully")
            self.is_connected = True
            
            # 메시지 수신 및 핑 태스크 시작
            asyncio.create_task(self._receive_messages())
            self.ping_task = asyncio.create_task(self._ping_loop())
            
            # 재연결 카운터 초기화
            self.reconnect_attempts = 0
            self.reconnect_interval = 2.0
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SFU server: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self) -> None:
        """SFU 서버 연결 종료."""
        logger.info("Disconnecting from SFU server")
        
        # 핑 태스크 취소
        if self.ping_task:
            self.ping_task.cancel()
            self.ping_task = None
        
        # 웹소켓 연결 종료
        if self.websocket:
            if not self.websocket.closed:
                await self.websocket.close()
            self.websocket = None
        
        # 세션 종료
        if self.session:
            await self.session.close()
            self.session = None
        
        self.is_connected = False
    
    async def reconnect(self) -> bool:
        """SFU 서버에 재연결.
        
        Returns:
            재연결 성공 여부
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Exceeded maximum reconnection attempts ({self.max_reconnect_attempts})")
            return False
        
        self.reconnect_attempts += 1
        
        # 이전 연결 종료
        await self.disconnect()
        
        # 지수 백오프로 대기
        backoff = min(self.reconnect_interval * (2 ** (self.reconnect_attempts - 1)), 
                      self.max_reconnect_interval)
        logger.info(f"Attempting to reconnect in {backoff:.1f} seconds (attempt {self.reconnect_attempts})")
        await asyncio.sleep(backoff)
        
        # 재연결 시도
        success = await self.connect()
        if success:
            # 재연결 성공 시 모든 스트림을 다시 구독
            for room_id, peer_id, producer_id in self.subscribed_streams:
                await self.subscribe_to_stream(room_id, peer_id, producer_id)
        
        return success
    
    def is_ready(self) -> bool:
        """서비스 준비 상태 확인.
        
        Returns:
            서비스 준비 여부
        """
        return self.is_connected
    
    def add_event_callback(self, callback: Callable[[SfuServiceEvent], Any]) -> None:
        """이벤트 콜백 추가.
        
        Args:
            callback: 콜백 함수
        """
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[SfuServiceEvent], Any]) -> None:
        """이벤트 콜백 제거.
        
        Args:
            callback: 콜백 함수
        """
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    async def subscribe_to_stream(
        self, 
        room_id: str, 
        peer_id: str, 
        producer_id: str
    ) -> bool:
        """스트림 구독.
        
        Args:
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            
        Returns:
            구독 성공 여부
        """
        if not self.is_ready():
            if not await self.connect():
                logger.error("Cannot subscribe to stream - SFU client not connected")
                return False
        
        logger.info(f"Subscribing to stream: room={room_id}, peer={peer_id}, producer={producer_id}")
        
        try:
            subscribe_message = {
                "type": "subscribe",
                "data": {
                    "room_id": room_id,
                    "peer_id": peer_id,
                    "producer_id": producer_id,
                }
            }
            
            await self.websocket.send_json(subscribe_message)
            
            # 구독 목록에 추가
            self.subscribed_streams.add((room_id, peer_id, producer_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to stream: {e}")
            return False
    
    async def unsubscribe_from_stream(
        self, 
        room_id: str, 
        peer_id: str, 
        producer_id: str
    ) -> bool:
        """스트림 구독 해제.
        
        Args:
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            
        Returns:
            구독 해제 성공 여부
        """
        if not self.is_ready():
            logger.warning("Cannot unsubscribe from stream - SFU client not connected")
            return False
        
        logger.info(f"Unsubscribing from stream: room={room_id}, peer={peer_id}, producer={producer_id}")
        
        try:
            unsubscribe_message = {
                "type": "unsubscribe",
                "data": {
                    "room_id": room_id,
                    "peer_id": peer_id,
                    "producer_id": producer_id,
                }
            }
            
            await self.websocket.send_json(unsubscribe_message)
            
            # 구독 목록에서 제거
            if (room_id, peer_id, producer_id) in self.subscribed_streams:
                self.subscribed_streams.remove((room_id, peer_id, producer_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from stream: {e}")
            return False
    
    async def process_stream_request(
        self,
        request: MediaStreamRequest
    ) -> Dict[str, Any]:
        """스트림 처리 요청.
        
        Args:
            request: 미디어 스트림 요청
            
        Returns:
            처리 결과
        """
        if request.stream_type != "audio":
            return {
                "status": "error",
                "message": "Only audio streams are supported",
            }
        
        success = await self.subscribe_to_stream(
            request.room_id,
            request.peer_id,
            request.producer_id
        )
        
        if success:
            return {
                "status": "accepted",
                "services_enabled": {
                    "speech_recognition": True,
                    "translation": True,
                    "emotion_analysis": True,
                },
            }
        else:
            return {
                "status": "error",
                "message": "Failed to subscribe to the stream",
            }
    
    async def send_event(self, event: SfuServiceEvent) -> bool:
        """이벤트 전송.
        
        Args:
            event: 전송할 이벤트
            
        Returns:
            전송 성공 여부
        """
        if not self.is_ready():
            logger.warning("Cannot send event - SFU client not connected")
            return False
        
        try:
            message = {
                "type": "event",
                "data": {
                    "event_type": event.type,
                    "event_data": event.data,
                    "room_id": event.room_id,
                    "peer_id": event.peer_id,
                }
            }
            
            if event.producer_id:
                message["data"]["producer_id"] = event.producer_id
            
            await self.websocket.send_json(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
            
            # 연결이 끊어진 경우 재연결 시도
            if self.websocket and self.websocket.closed:
                if self.reconnect_task is None or self.reconnect_task.done():
                    self.reconnect_task = asyncio.create_task(self.reconnect())
            
            return False
    
    async def _receive_messages(self) -> None:
        """웹소켓 메시지 수신 루프."""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                if message.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(message.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse message: {message.data}")
                elif message.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {message.data}")
                    break
                elif message.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break
                
        except asyncio.CancelledError:
            logger.debug("Message receive loop cancelled")
        except Exception as e:
            logger.error(f"Error in message receive loop: {e}")
        finally:
            # 연결이 끊어진 경우 재연결 시도
            if self.is_connected:
                self.is_connected = False
                if self.reconnect_task is None or self.reconnect_task.done():
                    self.reconnect_task = asyncio.create_task(self.reconnect())
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """메시지 처리.
        
        Args:
            message: 수신된 메시지
        """
        message_type = message.get("type", "unknown")
        
        if message_type == "pong":
            # 핑에 대한 응답
            self.last_pong_time = asyncio.get_event_loop().time()
            return
        
        elif message_type == "stream-data":
            # 스트림 데이터 수신
            data = message.get("data", {})
            room_id = data.get("room_id", "")
            peer_id = data.get("peer_id", "")
            producer_id = data.get("producer_id", "")
            
            event = SfuServiceEvent(
                type="stream-data",
                data={
                    "buffer": data.get("buffer", ""),  # base64 인코딩된 오디오 데이터
                    "sample_rate": data.get("sample_rate", 48000),
                    "channels": data.get("channels", 1),
                    "timestamp": data.get("timestamp", 0),
                },
                room_id=room_id,
                peer_id=peer_id,
                producer_id=producer_id,
            )
            
            # 이벤트 콜백 호출
            for callback in self.event_callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
        
        elif message_type == "stream-end":
            # 스트림 종료
            data = message.get("data", {})
            room_id = data.get("room_id", "")
            peer_id = data.get("peer_id", "")
            producer_id = data.get("producer_id", "")
            
            # 구독 목록에서 제거
            if (room_id, peer_id, producer_id) in self.subscribed_streams:
                self.subscribed_streams.remove((room_id, peer_id, producer_id))
            
            event = SfuServiceEvent(
                type="stream-end",
                data={},
                room_id=room_id,
                peer_id=peer_id,
                producer_id=producer_id,
            )
            
            # 이벤트 콜백 호출
            for callback in self.event_callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
    
    async def _ping_loop(self) -> None:
        """정기적인 핑을 보내는 루프."""
        while self.is_connected and self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send_json({"type": "ping"})
                await asyncio.sleep(self.ping_interval)
            except asyncio.CancelledError:
                logger.debug("Ping loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
                # 에러 발생 시 재연결 시도
                if self.reconnect_task is None or self.reconnect_task.done():
                    self.reconnect_task = asyncio.create_task(self.reconnect())
                break
    
    async def close(self) -> None:
        """리소스 정리."""
        # 모든 스트림 구독 해제
        for room_id, peer_id, producer_id in list(self.subscribed_streams):
            await self.unsubscribe_from_stream(room_id, peer_id, producer_id)
        
        # 연결 종료
        await self.disconnect() 