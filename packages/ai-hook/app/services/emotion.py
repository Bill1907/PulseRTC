"""감정 분석 서비스."""

import asyncio
import logging
import os
import random
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from app.core.config import settings
from app.schemas import EmotionCategory, EmotionResult

logger = logging.getLogger(__name__)


class EmotionAnalysisService:
    """감정 분석 서비스."""
    
    def __init__(self) -> None:
        """초기화."""
        self.model = None
        self.is_initialized = False
        self.model_name = settings.EMOTION_MODEL_NAME
        
        # 콜백 핸들러
        self.emotion_callbacks: List[Callable] = []
        
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
            # 실제 구현에서는 여기에 감정 분석 모델을 로드합니다.
            
            # 모델 디렉토리 확인
            model_dir = os.path.join(settings.AI_MODELS_DIR, "emotion")
            os.makedirs(model_dir, exist_ok=True)
            
            logger.info(f"Initializing emotion analysis service with model: {self.model_name}")
            
            # 현재는 목업 구현
            self.model = MockEmotionModel(self.model_name)
            self.is_initialized = True
            logger.info("Emotion analysis service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize emotion analysis service: {e}")
            return False

    def is_ready(self) -> bool:
        """서비스 준비 상태 확인.
        
        Returns:
            서비스 준비 여부
        """
        return self.is_initialized
    
    def add_emotion_callback(self, callback: Callable) -> None:
        """감정 분석 결과 콜백 추가.
        
        Args:
            callback: 콜백 함수
        """
        self.emotion_callbacks.append(callback)
    
    def remove_emotion_callback(self, callback: Callable) -> None:
        """감정 분석 결과 콜백 제거.
        
        Args:
            callback: 콜백 함수
        """
        if callback in self.emotion_callbacks:
            self.emotion_callbacks.remove(callback)
    
    async def analyze_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int, 
        room_id: str,
        peer_id: str,
        producer_id: str,
    ) -> Optional[EmotionResult]:
        """오디오 데이터의 감정 분석.
        
        Args:
            audio_data: 오디오 데이터 배열
            sample_rate: 샘플링 레이트
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            
        Returns:
            감정 분석 결과, 오류 시 None
        """
        if not self.is_initialized:
            if not self.initialize():
                logger.error("Emotion analysis service is not initialized")
                return None
        
        try:
            # 실제 구현에서는 여기서 모델을 사용하여 오디오를 분석합니다.
            result = await self.model.analyze(audio_data, sample_rate)
            
            # 결과 생성
            emotion_result = EmotionResult(
                primary_emotion=result["primary_emotion"],
                emotions=result["emotions"],
                confidence=result["confidence"],
            )
            
            # 콜백 호출
            for callback in self.emotion_callbacks:
                await callback(emotion_result, room_id, peer_id, producer_id)
            
            return emotion_result
            
        except Exception as e:
            logger.error(f"Error analyzing audio emotion: {e}")
            return None
    
    async def analyze_text(
        self, 
        text: str, 
        room_id: str,
        peer_id: str,
        producer_id: str,
    ) -> Optional[EmotionResult]:
        """텍스트 감정 분석.
        
        Args:
            text: 분석할 텍스트
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            
        Returns:
            감정 분석 결과, 오류 시 None
        """
        if not self.is_initialized:
            if not self.initialize():
                logger.error("Emotion analysis service is not initialized")
                return None
        
        try:
            # 실제 구현에서는 여기서 모델을 사용하여 텍스트를 분석합니다.
            result = await self.model.analyze_text(text)
            
            # 결과 생성
            emotion_result = EmotionResult(
                primary_emotion=result["primary_emotion"],
                emotions=result["emotions"],
                confidence=result["confidence"],
            )
            
            # 콜백 호출
            for callback in self.emotion_callbacks:
                await callback(emotion_result, room_id, peer_id, producer_id)
            
            return emotion_result
            
        except Exception as e:
            logger.error(f"Error analyzing text emotion: {e}")
            return None
    
    def close(self) -> None:
        """리소스 정리."""
        # 실제 구현에서는 여기서 모델을 언로드하고 리소스를 정리합니다.
        logger.info("Closing emotion analysis service")
        self.is_initialized = False
        self.model = None
        self.emotion_callbacks = []


class MockEmotionModel:
    """목업 감정 분석 모델."""
    
    def __init__(self, model_name: str) -> None:
        """초기화.
        
        Args:
            model_name: 모델 이름
        """
        self.model_name = model_name
        logger.info(f"Loaded mock emotion analysis model: {model_name}")
    
    async def analyze(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """오디오 데이터 감정 분석.
        
        Args:
            audio_data: 오디오 데이터 배열
            sample_rate: 샘플링 레이트
            
        Returns:
            감정 분석 결과
        """
        # 실제 모델이 아니므로 지연 시뮬레이션
        await asyncio.sleep(0.4)
        
        return self._generate_mock_emotion_result()
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """텍스트 감정 분석.
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과
        """
        # 실제 모델이 아니므로 지연 시뮬레이션
        await asyncio.sleep(0.2)
        
        # 특정 단어에 따른 감정 매핑 (간단한 규칙 기반 분석)
        if "안녕" in text or "반가" in text:
            primary = EmotionCategory.HAPPY
            weights = {
                EmotionCategory.HAPPY: 0.8,
                EmotionCategory.NEUTRAL: 0.15,
                EmotionCategory.SURPRISED: 0.05,
            }
        elif "슬퍼" in text or "아프" in text or "힘들" in text:
            primary = EmotionCategory.SAD
            weights = {
                EmotionCategory.SAD: 0.75,
                EmotionCategory.NEUTRAL: 0.15,
                EmotionCategory.FEARFUL: 0.1,
            }
        elif "화" in text or "짜증" in text or "분노" in text:
            primary = EmotionCategory.ANGRY
            weights = {
                EmotionCategory.ANGRY: 0.8,
                EmotionCategory.DISGUSTED: 0.15,
                EmotionCategory.NEUTRAL: 0.05,
            }
        else:
            return self._generate_mock_emotion_result()
        
        # 나머지 감정들에 대해 랜덤한 낮은 값 할당
        emotions = {category: 0.0 for category in EmotionCategory}
        for category, weight in weights.items():
            emotions[category] = weight
        
        return {
            "primary_emotion": primary,
            "emotions": emotions,
            "confidence": 0.85,
        }
    
    def _generate_mock_emotion_result(self) -> Dict[str, Any]:
        """목업 감정 분석 결과 생성.
        
        Returns:
            감정 분석 결과
        """
        # 감정별 가중치 생성 (랜덤)
        weights = {
            EmotionCategory.NEUTRAL: random.uniform(0.5, 0.8),
            EmotionCategory.HAPPY: random.uniform(0.0, 0.3),
            EmotionCategory.SAD: random.uniform(0.0, 0.1),
            EmotionCategory.ANGRY: random.uniform(0.0, 0.1),
            EmotionCategory.FEARFUL: random.uniform(0.0, 0.05),
            EmotionCategory.DISGUSTED: random.uniform(0.0, 0.05),
            EmotionCategory.SURPRISED: random.uniform(0.0, 0.1),
        }
        
        # 합계가 1이 되도록 정규화
        total = sum(weights.values())
        normalized_weights = {k: v / total for k, v in weights.items()}
        
        # 가장 높은 가중치의 감정을 주요 감정으로 선택
        primary_emotion = max(normalized_weights, key=normalized_weights.get)
        
        return {
            "primary_emotion": primary_emotion,
            "emotions": normalized_weights,
            "confidence": 0.9,
        } 