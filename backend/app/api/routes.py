from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.news_service import fetch_top_headlines
from ..services.alpha_service import fetch_daily
from ..services.upload_service import save_upload

router = APIRouter()

@router.post("/ingest/news")
def ingest_news(country: str = "us", q: str | None = None):
    result = fetch_top_headlines(country=country, q=q)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/ingest/alpha")
def ingest_alpha(symbol: str = "AAPL"):
    result = fetch_daily(symbol=symbol)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    name = file.filename.lower()
    kind = "pdf" if name.endswith(".pdf") else "csv" if name.endswith(".csv") else "txt" if name.endswith(".txt") else "other"
    return save_upload(file.filename, data, kind)