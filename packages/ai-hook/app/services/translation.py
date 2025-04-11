"""번역 서비스."""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings
from app.schemas import TranslationResult

logger = logging.getLogger(__name__)


class TranslationService:
    """번역 서비스."""
    
    def __init__(self) -> None:
        """초기화."""
        self.model = None
        self.is_initialized = False
        self.source_lang = settings.TRANSLATION_SOURCE_LANG
        self.target_lang = settings.TRANSLATION_TARGET_LANG
        self.model_name = settings.TRANSLATION_MODEL_NAME
        
        # 콜백 핸들러
        self.translation_callbacks: List[Callable] = []
        
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
            # 실제 구현에서는 여기에 번역 모델을 로드합니다.
            # 예: mBART, M2M100 등
            
            # 모델 디렉토리 확인
            model_dir = os.path.join(settings.AI_MODELS_DIR, "translation")
            os.makedirs(model_dir, exist_ok=True)
            
            logger.info(f"Initializing translation service with model: {self.model_name}")
            
            # 현재는 목업 구현
            self.model = MockTranslationModel(
                self.model_name, self.source_lang, self.target_lang
            )
            self.is_initialized = True
            logger.info("Translation service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize translation service: {e}")
            return False

    def is_ready(self) -> bool:
        """서비스 준비 상태 확인.
        
        Returns:
            서비스 준비 여부
        """
        return self.is_initialized
    
    def add_translation_callback(self, callback: Callable) -> None:
        """번역 결과 콜백 추가.
        
        Args:
            callback: 콜백 함수
        """
        self.translation_callbacks.append(callback)
    
    def remove_translation_callback(self, callback: Callable) -> None:
        """번역 결과 콜백 제거.
        
        Args:
            callback: 콜백 함수
        """
        if callback in self.translation_callbacks:
            self.translation_callbacks.remove(callback)
    
    async def translate_text(
        self, 
        text: str, 
        room_id: str,
        peer_id: str,
        producer_id: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> Optional[TranslationResult]:
        """텍스트 번역.
        
        Args:
            text: 번역할 텍스트
            room_id: 방 ID
            peer_id: 피어 ID
            producer_id: 프로듀서 ID
            source_lang: 소스 언어 (None인 경우 기본값 사용)
            target_lang: 타겟 언어 (None인 경우 기본값 사용)
            
        Returns:
            번역 결과, 오류 시 None
        """
        if not self.is_initialized:
            if not self.initialize():
                logger.error("Translation service is not initialized")
                return None
        
        try:
            # 소스/타겟 언어 설정
            src_lang = source_lang or self.source_lang
            tgt_lang = target_lang or self.target_lang
            
            # 실제 구현에서는 여기서 모델을 사용하여 텍스트를 번역합니다.
            result = await self.model.translate(text, src_lang, tgt_lang)
            
            # 결과 생성
            translation_result = TranslationResult(
                source_text=text,
                translated_text=result["translated_text"],
                source_lang=src_lang,
                target_lang=tgt_lang,
                confidence=result.get("confidence"),
            )
            
            # 콜백 호출
            for callback in self.translation_callbacks:
                await callback(translation_result, room_id, peer_id, producer_id)
            
            return translation_result
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return None
    
    def close(self) -> None:
        """리소스 정리."""
        # 실제 구현에서는 여기서 모델을 언로드하고 리소스를 정리합니다.
        logger.info("Closing translation service")
        self.is_initialized = False
        self.model = None
        self.translation_callbacks = []


class MockTranslationModel:
    """목업 번역 모델."""
    
    def __init__(self, model_name: str, source_lang: str, target_lang: str) -> None:
        """초기화.
        
        Args:
            model_name: 모델 이름
            source_lang: 소스 언어 코드
            target_lang: 타겟 언어 코드
        """
        self.model_name = model_name
        self.source_lang = source_lang
        self.target_lang = target_lang
        logger.info(
            f"Loaded mock translation model: {model_name} "
            f"for {source_lang} -> {target_lang}"
        )
    
    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
        """텍스트 번역.
        
        Args:
            text: 번역할 텍스트
            source_lang: 소스 언어
            target_lang: 타겟 언어
            
        Returns:
            번역 결과
        """
        # 실제 모델이 아니므로 지연 시뮬레이션
        await asyncio.sleep(0.3)
        
        # 목업 번역 결과
        translations = {
            "ko": {
                "en": {
                    "안녕하세요": "Hello",
                    "테스트 음성 인식입니다": "This is a test speech recognition",
                    "안녕하세요, 테스트 음성 인식입니다.": "Hello, this is a test speech recognition.",
                },
                "ja": {
                    "안녕하세요": "こんにちは",
                    "테스트 음성 인식입니다": "テスト音声認識です",
                    "안녕하세요, 테스트 음성 인식입니다.": "こんにちは、テスト音声認識です。",
                },
            }
        }
        
        # 번역 매핑에서 결과 찾기
        if source_lang in translations and target_lang in translations[source_lang]:
            if text in translations[source_lang][target_lang]:
                translated = translations[source_lang][target_lang][text]
            else:
                # 간단한 대체 번역 - 실제 번역 모델은 더 정교합니다
                translated = f"[{target_lang}] {text}"
        else:
            translated = f"[{target_lang}] {text}"
        
        return {
            "translated_text": translated,
            "confidence": 0.92,
        } 