"""
API 문서화 헬퍼 모듈
FastAPI OpenAPI 스키마 개선 및 문서화 자동화 도구
"""
from typing import Dict, Any, List, Optional, Callable
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import Tag
import logging

logger = logging.getLogger(__name__)

class APIDocumentationHelper:
    """API 문서화 개선 헬퍼 클래스"""
    
    @staticmethod
    def create_custom_openapi(
        app: FastAPI,
        title: str,
        version: str,
        description: str,
        tags_metadata: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """커스텀 OpenAPI 스키마 생성"""
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
        )
        
        # 서버 정보 추가
        if servers:
            openapi_schema["servers"] = servers
        else:
            openapi_schema["servers"] = [
                {"url": "http://localhost:8000", "description": "개발 서버"},
                {"url": "https://api.example.com", "description": "프로덕션 서버"}
            ]
        
        # 태그 메타데이터 추가
        if tags_metadata:
            openapi_schema["tags"] = tags_metadata
        
        # 보안 스키마 추가
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT 토큰을 이용한 인증"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API 키를 이용한 인증"
            }
        }
        
        # 공통 응답 스키마 추가
        openapi_schema["components"]["schemas"].update({
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "description": "에러 메시지"},
                    "error_code": {"type": "string", "description": "에러 코드"},
                    "details": {"type": "object", "description": "상세 정보"}
                },
                "required": ["error"]
            },
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "서비스 상태"},
                    "service": {"type": "string", "description": "서비스 이름"},
                    "version": {"type": "string", "description": "버전"},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["status", "service", "version"]
            }
        })
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    @staticmethod
    def get_sasb_service_tags() -> List[Dict[str, Any]]:
        """SASB 서비스 태그 메타데이터"""
        return [
            {
                "name": "Analysis",
                "description": "ESG 뉴스 분석 및 SASB 매핑 관련 API"
            },
            {
                "name": "Dashboard",
                "description": "대시보드 및 시스템 상태 관리 API"
            },
            {
                "name": "Cache",
                "description": "캐시 관리 및 데이터 저장 API"
            },
            {
                "name": "System",
                "description": "시스템 헬스체크 및 메타데이터 API"
            },
            {
                "name": "Worker",
                "description": "백그라운드 작업 및 스케줄링 API"
            }
        ]
    
    @staticmethod
    def get_material_service_tags() -> List[Dict[str, Any]]:
        """Material 서비스 태그 메타데이터"""
        return [
            {
                "name": "Materiality Analysis",
                "description": "중대성 평가 변화 분석 및 업데이트 제안 API"
            },
            {
                "name": "File Management",
                "description": "중대성 평가 파일 업로드 및 관리 API"
            },
            {
                "name": "Recommendations",
                "description": "개선 사항 및 액션 아이템 추천 API"
            },
            {
                "name": "Industry Analysis",
                "description": "산업별 중대성 이슈 동향 분석 API"
            }
        ]
    
    @staticmethod
    def get_gateway_service_tags() -> List[Dict[str, Any]]:
        """Gateway 서비스 태그 메타데이터"""
        return [
            {
                "name": "Authentication",
                "description": "사용자 인증 및 토큰 관리 API"
            },
            {
                "name": "Proxy",
                "description": "마이크로서비스 프록시 및 라우팅 API"
            },
            {
                "name": "Health",
                "description": "전체 시스템 헬스체크 API"
            }
        ]

class ResponseSchemaHelper:
    """응답 스키마 정의 헬퍼 클래스"""
    
    @staticmethod
    def create_analysis_response_schema() -> Dict[str, Any]:
        """분석 결과 응답 스키마"""
        return {
            "type": "object",
            "properties": {
                "analysis_metadata": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "분석 대상 회사명"},
                        "analysis_year": {"type": "integer", "description": "분석 년도"},
                        "analysis_date": {"type": "string", "format": "date-time", "description": "분석 실행 일시"},
                        "status": {"type": "string", "enum": ["success", "failure"], "description": "분석 상태"}
                    }
                },
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic_name": {"type": "string", "description": "토픽명"},
                            "priority": {"type": "number", "description": "우선순위 점수"},
                            "change_magnitude": {"type": "number", "description": "변화 강도"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "신뢰도"}
                        }
                    }
                },
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "추천 타입"},
                            "action": {"type": "string", "description": "권장 액션"},
                            "rationale": {"type": "string", "description": "근거"}
                        }
                    }
                }
            },
            "required": ["analysis_metadata", "results"]
        }
    
    @staticmethod
    def create_news_analysis_response_schema() -> Dict[str, Any]:
        """뉴스 분석 결과 응답 스키마"""
        return {
            "type": "object",
            "properties": {
                "total_articles": {"type": "integer", "description": "분석된 총 기사 수"},
                "analysis_period": {"type": "string", "description": "분석 기간"},
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "기사 제목"},
                            "content": {"type": "string", "description": "기사 내용"},
                            "link": {"type": "string", "format": "uri", "description": "기사 링크"},
                            "published_at": {"type": "string", "format": "date", "description": "발행일"},
                            "sentiment": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string", "enum": ["긍정", "부정", "중립"], "description": "감정 라벨"},
                                    "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "신뢰도"}
                                }
                            }
                        }
                    }
                }
            }
        }

class ExampleGenerator:
    """API 예제 생성 헬퍼 클래스"""
    
    @staticmethod
    def get_analysis_request_examples() -> Dict[str, Any]:
        """분석 요청 예제"""
        return {
            "basic_analysis": {
                "summary": "기본 중대성 분석",
                "value": {
                    "company_name": "삼성전자",
                    "analysis_year": 2024,
                    "keywords": ["ESG", "지속가능경영", "탄소중립"]
                }
            },
            "detailed_analysis": {
                "summary": "상세 키워드 조합 분석",
                "value": {
                    "company_name": "LG화학",
                    "analysis_year": 2024,
                    "domain_keywords": ["환경", "사회", "지배구조"],
                    "issue_keywords": ["투자", "정책", "규제", "기술혁신"],
                    "max_combinations": 10
                }
            }
        }
    
    @staticmethod
    def get_analysis_response_examples() -> Dict[str, Any]:
        """분석 응답 예제"""
        return {
            "successful_analysis": {
                "summary": "성공적인 분석 결과",
                "value": {
                    "analysis_metadata": {
                        "company_name": "삼성전자",
                        "analysis_year": 2024,
                        "analysis_date": "2024-01-15T09:30:00Z",
                        "status": "success"
                    },
                    "results": [
                        {
                            "topic_name": "탄소배출 감축",
                            "priority": 9.2,
                            "change_magnitude": 0.15,
                            "confidence": 0.85
                        },
                        {
                            "topic_name": "공급망 관리",
                            "priority": 8.7,
                            "change_magnitude": -0.05,
                            "confidence": 0.78
                        }
                    ],
                    "recommendations": [
                        {
                            "type": "priority_review",
                            "action": "탄소배출 감축 우선순위 상향 검토",
                            "rationale": "뉴스 언급도 15% 증가, 정책 강화 영향"
                        }
                    ]
                }
            },
            "error_response": {
                "summary": "분석 실패 응답",
                "value": {
                    "error": "분석 처리 중 오류가 발생했습니다",
                    "error_code": "ANALYSIS_FAILED",
                    "details": {
                        "company_name": "Unknown Corp",
                        "reason": "기업 정보를 찾을 수 없습니다"
                    }
                }
            }
        }

def setup_api_documentation(
    app: FastAPI,
    service_name: str,
    service_description: str,
    version: str = "1.0.0"
) -> None:
    """API 문서화 설정 적용"""
    
    # 서비스별 태그 메타데이터 선택
    if "sasb" in service_name.lower():
        tags_metadata = APIDocumentationHelper.get_sasb_service_tags()
    elif "material" in service_name.lower():
        tags_metadata = APIDocumentationHelper.get_material_service_tags()
    elif "gateway" in service_name.lower():
        tags_metadata = APIDocumentationHelper.get_gateway_service_tags()
    else:
        tags_metadata = []
    
    # 커스텀 OpenAPI 스키마 적용
    def custom_openapi():
        return APIDocumentationHelper.create_custom_openapi(
            app=app,
            title=service_name,
            version=version,
            description=service_description,
            tags_metadata=tags_metadata
        )
    
    app.openapi = custom_openapi
    
    # 스키마 컴포넌트 등록
    if hasattr(app, 'add_api_schema'):
        app.add_api_schema("AnalysisResponse", ResponseSchemaHelper.create_analysis_response_schema())
        app.add_api_schema("NewsAnalysisResponse", ResponseSchemaHelper.create_news_analysis_response_schema())
    
    logger.info(f"✅ {service_name} API 문서화 설정 완료")

# FastAPI 라우터 데코레이터 확장
def documented_route(
    path: str,
    method: str = "GET",
    summary: str = "",
    description: str = "",
    tags: List[str] = None,
    responses: Dict[int, Dict[str, Any]] = None
):
    """문서화가 강화된 라우터 데코레이터"""
    def decorator(func: Callable):
        # FastAPI 라우터 설정에 문서화 정보 추가
        func.__doc__ = description
        func.__summary__ = summary
        func.__tags__ = tags or []
        func.__responses__ = responses or {}
        return func
    return decorator 