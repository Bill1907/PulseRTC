"""스트림 데이터 관련 스키마."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema


class MediaKind(str, Enum):
    """미디어 타입."""
    
    AUDIO = "audio"
    VIDEO = "video"


class MediaStreamRequest(BaseSchema):
    """미디어 스트림 요청."""
    
    roomId: str
    peerId: str
    producerId: str
    kind: MediaKind
    metadata: Optional[Dict[str, Any]] = None


class TranscriptionResult(BaseSchema):
    """음성 인식 결과."""
    
    text: str
    confidence: float
    is_final: bool = False
    segments: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None


class TranslationResult(BaseSchema):
    """번역 결과."""
    
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: Optional[float] = None


class EmotionCategory(str, Enum):
    """감정 카테고리."""
    
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"


class EmotionResult(BaseSchema):
    """감정 분석 결과."""
    
    primary_emotion: EmotionCategory
    emotions: Dict[EmotionCategory, float]
    confidence: float


class AIHookEventType(str, Enum):
    """AI Hook 이벤트 타입."""
    
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    EMOTION = "emotion"
    ERROR = "error"


class AIHookEvent(BaseSchema):
    """AI Hook 이벤트."""
    
    type: AIHookEventType
    roomId: str
    peerId: str
    producerId: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] 