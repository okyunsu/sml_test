from pydantic import BaseModel
from typing import List, Optional

class ESGIssueRequest(BaseModel):
    file_path: str  # 서버 내부 경로 (PDF)

class ESGIssue(BaseModel):
    id: str
    text: str
    keywords: List[str]
    mapped_gri: Optional[str]
    score: float
    source_file: str