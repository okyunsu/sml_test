from fastapi import FastAPI
from app.api.esg_issue_router import router as esg_issue_router

app = FastAPI()
app.include_router(esg_issue_router)