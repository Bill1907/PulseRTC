"""음성 인식 서비스."""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from app.core.config import settings
from app.schemas import TranscriptionResult

logger = logging.getLogger(__name__)


class SpeechRecognitionService:
    """음성 인식 서비스."""
    
    def __init__(self) -> None:
        """초기화."""
        self.model = None
        self.is_initialized = False
        self.language = settings.ASR_LANGUAGE
        self.model_name = settings.ASR_MODEL_NAME
        
        # 콜백 핸들러
        self.transcription_callbacks: List[Callable] = []
        
        # 초기화 시도
        self.initialize()

    def initialize(self) -> bool:
        """서비스 초기화.
        
        Returns:
            초기화 성공 여부
        """
        if self.is_initialized:
            return True
        
        try:
            # 실제 구현에서는 여기에 음성 인식 모델을 로드합니다.
            # 예: whisper, wav2vec 등
            
            # 모델 디렉토리 확인
            model_dir = os.path.join(settings.AI_MODELS_DIR, "asr")
            os.makedirs(model_dir, exist_ok=True)
            
            logger.info(f"Initializing ASR service with model: {self.model_name}")
            
            # 현재는 목업 구현
            self.model = MockASRModel(self.model_name, self.language)
            self.is_initialized = True
            logger.info("ASR service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ASR service: {e}")
            return False

    def is_ready(self) -> bool:
        """서비스 준비 상태 확인.
        
        Returns:
            서비스 준비 여부
        """
        return self.is_initialized
    
    def add_transcription_callback(self, callback: Callable) -> None:
        """전사 결과 콜백 추가.
        
        Args:
            callback: 콜백 함수
        """
        self.transcription_callbacks.append(callback)
    
    def remove_transcription_callback(self, callback: Callable) -> None:
        """전사 결과 콜백 제거.
        
        Args:
            callback: 콜백 함수
        """
        if callback in self.transcription_callbacks:
            self.transcription_callbacks.remove(callback)
    
    async def process_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int, 
        room_id: str,
        peer_id: str,
        producer_id: str,
    ) -> Optional[TranscriptionResult]:
        """오디오 데이터 처리.
        
        Args:
            audio_data: 오디오 데이터 배열
            sample_rate: 샘플링 레이트
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            
        Returns:
            전사 결과, 오류 시 None
        """
        if not self.is_initialized:
            if not self.initialize():
                logger.error("ASR service is not initialized")
                return None
        
        try:
            # 실제 구현에서는 여기서 모델을 사용하여 오디오를 처리합니다.
            result = await self.model.transcribe(audio_data, sample_rate)
            
            # 결과 생성
            transcription_result = TranscriptionResult(
                text=result["text"],
                confidence=result["confidence"],
                is_final=result["is_final"],
                segments=result.get("segments"),
                language=self.language,
            )
            
            # 콜백 호출
            for callback in self.transcription_callbacks:
                await callback(transcription_result, room_id, peer_id, producer_id)
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    
    def close(self) -> None:
        """리소스 정리."""
        # 실제 구현에서는 여기서 모델을 언로드하고 리소스를 정리합니다.
        logger.info("Closing ASR service")
        self.is_initialized = False
        self.model = None
        self.transcription_callbacks = []


class MockASRModel:
    """목업 ASR 모델."""
    
    def __init__(self, model_name: str, language: str) -> None:
        """초기화.
        
        Args:
            model_name: 모델 이름
            language: 언어 코드
        """
        self.model_name = model_name
        self.language = language
        logger.info(f"Loaded mock ASR model: {model_name} for language: {language}")
    
    async def transcribe(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """오디오 데이터 전사.
        
        Args:
            audio_data: 오디오 데이터 배열
            sample_rate: 샘플링 레이트
            
        Returns:
            전사 결과
        """
        # 실제 모델이 아니므로 지연 시뮬레이션
        await asyncio.sleep(0.5)
        
        # 목업 결과 반환
        return {
            "text": "안녕하세요, 테스트 음성 인식입니다.",
            "confidence": 0.95,
            "is_final": True,
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "안녕하세요,",
                    "confidence": 0.97,
                },
                {
                    "id": 1,
                    "start": 2.0,
                    "end": 4.0,
                    "text": "테스트 음성 인식입니다.",
                    "confidence": 0.93,
                },
            ],
        } 