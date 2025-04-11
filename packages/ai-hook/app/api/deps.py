"""API 의존성 모듈."""

from typing import Generator

from fastapi import Depends

from app.services.asr import SpeechRecognitionService
from app.services.emotion import EmotionAnalysisService
from app.services.sfu_client import SfuClient
from app.services.translation import TranslationService


def get_speech_recognition_service() -> Generator[SpeechRecognitionService, None, None]:
    """음성 인식 서비스 의존성.
    
    Returns:
        SpeechRecognitionService 인스턴스
    """
    service = SpeechRecognitionService()
    try:
        yield service
    finally:
        service.close()


def get_translation_service() -> Generator[TranslationService, None, None]:
    """번역 서비스 의존성.
    
    Returns:
        TranslationService 인스턴스
    """
    service = TranslationService()
    try:
        yield service
    finally:
        service.close()


def get_emotion_analysis_service() -> Generator[EmotionAnalysisService, None, None]:
    """감정 분석 서비스 의존성.
    
    Returns:
        EmotionAnalysisService 인스턴스
    """
    service = EmotionAnalysisService()
    try:
        yield service
    finally:
        service.close()


def get_sfu_client() -> Generator[SfuClient, None, None]:
    """SFU 클라이언트 의존성.
    
    Returns:
        SfuClient 인스턴스
    """
    client = SfuClient()
    try:
        yield client
    finally:
        client.close() 