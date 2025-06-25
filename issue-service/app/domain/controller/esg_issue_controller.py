import uuid
import shutil
from fastapi import UploadFile, HTTPException
from typing import Dict, Any
from app.domain.service.esg_issue_service import (
    extract_esg_issues_from_pdf,
    extract_esg_issues_from_pdf_with_local_ai,
    save_issues_to_json,
    save_issues_to_csv,
    save_clusters_to_json,
    cluster_keywords
)
from app.domain.service.materiality_assessment_service import (
    MaterialityAssessmentService,
    QuantitativeData,
    NewsData,
    save_materiality_results
)
import os
from datetime import datetime

class ESGIssueController:
    @staticmethod
    def extract_issues(file: UploadFile):
        """기존 키워드 기반 ESG 이슈 추출 (호환성 유지)"""
        try:
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            issues = extract_esg_issues_from_pdf(temp_path)
            os.remove(temp_path)

            issue_id = str(uuid.uuid4())[:8]

            json_path = save_issues_to_json(issues, f"esg_issues_{issue_id}.json")
            csv_path = save_issues_to_csv(issues, f"esg_issues_{issue_id}.csv")

            clustered, representatives = cluster_keywords(issues)
            clusters_path = save_clusters_to_json(clustered, representatives, f"clusters_{issue_id}.json")

            return {
                "issue_count": len(issues),
                "json_path": json_path,
                "csv_path": csv_path,
                "clusters_json_path": clusters_path,
                "issues": issues,
                "clustered_keywords": clustered,
                "cluster_representatives": representatives
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이슈 추출 실패: {str(e)}")
    
    @staticmethod
    def extract_issues_with_local_ai(file: UploadFile, use_ai_model: bool = True):
        """🤖 로컬 AI 모델을 사용한 향상된 ESG 이슈 추출"""
        try:
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 로컬 AI 모델 기반 이슈 추출
            issues = extract_esg_issues_from_pdf_with_local_ai(temp_path, use_ai_model=use_ai_model)
            os.remove(temp_path)

            issue_id = str(uuid.uuid4())[:8]
            method_suffix = "local_ai" if use_ai_model else "keyword"

            # 결과 저장
            json_path = save_issues_to_json(issues, f"esg_issues_{method_suffix}_{issue_id}.json")
            csv_path = save_issues_to_csv(issues, f"esg_issues_{method_suffix}_{issue_id}.csv")

            # 키워드 클러스터링
            clustered, representatives = cluster_keywords(issues)
            clusters_path = save_clusters_to_json(clustered, representatives, f"clusters_{method_suffix}_{issue_id}.json")

            return {
                "method": "로컬 AI 모델 기반" if use_ai_model else "키워드 기반",
                "model_path": "/app/models" if use_ai_model else "N/A",
                "issue_count": len(issues),
                "json_path": json_path,
                "csv_path": csv_path,
                "clusters_json_path": clusters_path,
                "issues": issues,
                "clustered_keywords": clustered,
                "cluster_representatives": representatives,
                "performance_metrics": {
                    "total_paragraphs_processed": len([issue for issue in issues]),
                    "avg_confidence_score": round(sum(issue.score for issue in issues) / len(issues), 3) if issues else 0,
                    "high_confidence_issues": len([issue for issue in issues if issue.score > 0.8])
                }
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"로컬 AI 기반 이슈 추출 실패: {str(e)}")

    @staticmethod
    def conduct_materiality_assessment(
        file: UploadFile, 
        quantitative_data: Dict[str, Any],
        news_data: Dict[str, Any] = None
    ):
        """🎯 AI 기반 중대성평가 수행"""
        try:
            # 1. ESG 이슈 추출
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            issues = extract_esg_issues_from_pdf_with_local_ai(temp_path, use_ai_model=True)
            os.remove(temp_path)

            # 2. 정량데이터 구조화
            quant_data = QuantitativeData(
                revenue=quantitative_data.get("revenue", 1000000),
                costs=quantitative_data.get("costs", 100000),
                carbon_emissions=quantitative_data.get("carbon_emissions", 50000),
                water_usage=quantitative_data.get("water_usage", 10000),
                waste_generation=quantitative_data.get("waste_generation", 5000),
                employee_count=quantitative_data.get("employee_count", 1000),
                safety_incidents=quantitative_data.get("safety_incidents", 5)
            )

            # 3. 뉴스데이터 구조화 (선택사항)
            news_data_list = []
            if news_data and "articles" in news_data:
                for article in news_data["articles"]:
                    news_item = NewsData(
                        content=article.get("content", ""),
                        source=article.get("source", "Unknown"),
                        publish_date=datetime.fromisoformat(article.get("publish_date", datetime.now().isoformat())),
                        mentions=article.get("mentions", 1),
                        audience_reach=article.get("audience_reach", 1000),
                        source_credibility=article.get("source_credibility", 0.5)
                    )
                    news_data_list.append(news_item)

            # 4. 중대성평가 수행
            assessment_service = MaterialityAssessmentService()
            materiality_results = assessment_service.conduct_materiality_assessment(
                esg_issues=issues,
                quant_data=quant_data,
                news_data_list=news_data_list
            )

            # 5. 매트릭스 데이터 생성
            matrix_data = assessment_service.create_materiality_matrix_data(materiality_results)

            # 6. 결과 저장
            assessment_id = str(uuid.uuid4())[:8]
            materiality_path = save_materiality_results(
                materiality_results, 
                f"materiality_assessment_{assessment_id}.json"
            )

            # 7. 기본 이슈 파일도 저장
            json_path = save_issues_to_json(issues, f"esg_issues_materiality_{assessment_id}.json")
            csv_path = save_issues_to_csv(issues, f"esg_issues_materiality_{assessment_id}.csv")

            return {
                "assessment_id": assessment_id,
                "method": "AI 기반 중대성평가",
                "total_issues": len(issues),
                "materiality_summary": {
                    "high_priority": len([r for r in materiality_results if r.materiality_level == "High"]),
                    "medium_priority": len([r for r in materiality_results if r.materiality_level == "Medium"]),
                    "low_priority": len([r for r in materiality_results if r.materiality_level == "Low"])
                },
                "top_priority_issues": [
                    {
                        "text": r.issue_text[:100] + "..." if len(r.issue_text) > 100 else r.issue_text,
                        "business_impact": r.business_impact_score,
                        "stakeholder_interest": r.stakeholder_interest_score,
                        "level": r.materiality_level,
                        "gri": r.gri_mapping,
                        "recommendations": r.recommendations[:2]  # 상위 2개 권고사항만
                    }
                    for r in materiality_results[:10]  # 상위 10개만
                ],
                "matrix_data": matrix_data,
                "files": {
                    "materiality_assessment": materiality_path,
                    "esg_issues_json": json_path,
                    "esg_issues_csv": csv_path
                },
                "data_sources": {
                    "esg_report": file.filename,
                    "quantitative_data": bool(quantitative_data),
                    "news_data": len(news_data_list) if news_data_list else 0
                }
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"중대성평가 실패: {str(e)}")