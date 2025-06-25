from fastapi import APIRouter, UploadFile, File, Query, Form
from typing import Optional, Dict, Any
import json
from app.domain.controller.esg_issue_controller import ESGIssueController

router = APIRouter(prefix="/esg/issues", tags=["ESG Issues"])

@router.post("/")
def extract_issues(file: UploadFile = File(...)):
    """기존 키워드 기반 ESG 이슈 추출"""
    return ESGIssueController.extract_issues(file)

@router.post("/ai")
def extract_issues_with_local_ai(
    file: UploadFile = File(...),
    use_ai_model: bool = Query(True, description="로컬 AI 모델 사용 여부 (False시 키워드 기반)")
):
    """🤖 로컬 AI 모델을 사용한 향상된 ESG 이슈 추출
    
    - **file**: ESG 보고서 PDF 파일
    - **use_ai_model**: True(기본값) - 로컬 AI 모델 사용, False - 키워드 기반 사용
    
    **로컬 AI 모델 장점:**
    - 네트워크 연결 불필요 (오프라인 작동)
    - 빠른 응답 속도
    - 더 정확한 ESG 관련 내용 식별
    - 컨텍스트 기반 분류
    - 신뢰도 점수 제공
    - 50개 ESG 보고서로 파인튜닝된 BERT 모델 사용
    """
    return ESGIssueController.extract_issues_with_local_ai(file, use_ai_model)

@router.post("/materiality-assessment")
def conduct_materiality_assessment(
    file: UploadFile = File(...),
    quantitative_data: str = Form(...),
    news_data: Optional[str] = Form(None)
):
    """🎯 AI 기반 중대성평가 수행
    
    **통합 중대성평가 시스템:**
    - ESG 보고서 AI 분석
    - 정량데이터 기반 비즈니스 임팩트 계산
    - 뉴스데이터 기반 이해관계자 관심도 분석
    - 중대성 매트릭스 생성 및 우선순위 도출
    
    **입력 데이터:**
    - **file**: ESG 보고서 PDF
    - **quantitative_data**: 정량데이터 JSON
      ```json
      {
        "revenue": 1000000,
        "costs": 100000,
        "carbon_emissions": 50000,
        "water_usage": 10000,
        "waste_generation": 5000,
        "employee_count": 1000,
        "safety_incidents": 5
      }
      ```
    - **news_data**: 뉴스데이터 JSON (선택사항)
      ```json
      {
        "articles": [
          {
            "content": "뉴스 내용...",
            "source": "조선일보",
            "publish_date": "2024-01-01T00:00:00",
            "mentions": 10,
            "audience_reach": 100000,
            "source_credibility": 0.8
          }
        ]
      }
      ```
    
    **출력 결과:**
    - 중대성 수준별 이슈 분류 (High/Medium/Low)
    - 비즈니스 임팩트 vs 이해관계자 관심도 매트릭스
    - 우선순위별 권고사항
    - GRI 표준 매핑
    """
    try:
        # JSON 파싱
        quant_data_dict = json.loads(quantitative_data)
        news_data_dict = json.loads(news_data) if news_data else None
        
        return ESGIssueController.conduct_materiality_assessment(
            file=file,
            quantitative_data=quant_data_dict,
            news_data=news_data_dict
        )
    except json.JSONDecodeError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {str(e)}")

@router.get("/health")
def health_check():
    """서비스 상태 확인"""
    import os
    model_exists = os.path.exists("/app/models/adapter_config.json")
    
    return {
        "status": "healthy",
        "service": "ESG Issue Extraction Service",
        "local_ai_model": "esg-bert-bd2761a4",
        "model_available": model_exists,
        "model_path": "/app/models"
    }