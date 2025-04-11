"""API 라우터 설정."""

from fastapi import APIRouter

from app.api.endpoints import health, stream

# API 라우터
api_router = APIRouter()

# 헬스 체크
api_router.include_router(health.router, tags=["health"])

# 스트림 처리
api_router.include_router(stream.router, prefix="/stream", tags=["stream"]) 