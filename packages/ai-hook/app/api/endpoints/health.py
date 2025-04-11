"""헬스 체크 API 라우터."""

from fastapi import APIRouter, Depends, HTTPException, status

from app import __version__
from app.schemas import HealthResponse
from app.services.asr import SpeechRecognitionService
from app.services.emotion import EmotionAnalysisService
from app.services.translation import TranslationService
from app.api.deps import (
    get_speech_recognition_service,
    get_translation_service,
    get_emotion_analysis_service,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서비스 상태를 확인합니다.",
)
async def health_check(
    asr_service: SpeechRecognitionService = Depends(get_speech_recognition_service),
    translation_service: TranslationService = Depends(get_translation_service),
    emotion_service: EmotionAnalysisService = Depends(get_emotion_analysis_service),
) -> HealthResponse:
    """헬스 체크 API.
    
    Args:
        asr_service: 음성 인식 서비스
        translation_service: 번역 서비스
        emotion_service: 감정 분석 서비스
        
    Returns:
        HealthResponse: 서비스 상태 정보
    """
    # 서비스 상태 확인
    services_status = {
        "asr": asr_service.is_ready(),
        "translation": translation_service.is_ready(),
        "emotion": emotion_service.is_ready(),
    }
    
    # 모든 서비스가 준비되었는지 확인
    if not all(services_status.values()):
        # 어떤 서비스가 준비되지 않았는지 확인
        not_ready = [name for name, ready in services_status.items() if not ready]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Services not ready: {', '.join(not_ready)}",
        )
    
    return HealthResponse(version=__version__) 