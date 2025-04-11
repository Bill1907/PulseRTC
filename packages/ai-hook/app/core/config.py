"""설정 관리 모듈."""

import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PulseRTC AI Hook"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """CORS 오리진 목록 조립.
        
        Args:
            v: CORS 오리진 문자열 또는 목록
            
        Returns:
            처리된 CORS 오리진 목록
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    WORKERS: int = 1
    LOG_LEVEL: str = "info"
    
    # 웹소켓 설정
    WS_HEARTBEAT_INTERVAL: int = 30  # 초 단위
    
    # AI 모델 설정
    AI_MODELS_DIR: str = "models"
    ENABLE_SPEECH_RECOGNITION: bool = True
    ENABLE_TRANSLATION: bool = True
    ENABLE_EMOTION_ANALYSIS: bool = True
    
    # 음성 인식 설정
    ASR_MODEL_NAME: str = "small"  # small, medium, large
    ASR_LANGUAGE: str = "ko"
    
    # 번역 설정
    TRANSLATION_MODEL_NAME: str = "small"
    TRANSLATION_SOURCE_LANG: str = "ko"
    TRANSLATION_TARGET_LANG: str = "en"
    
    # 감정 분석 설정
    EMOTION_MODEL_NAME: str = "small"
    
    # SFU 연결 설정
    SFU_WS_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


settings = Settings() 