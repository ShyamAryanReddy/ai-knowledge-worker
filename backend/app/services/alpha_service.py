import requests
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from ..db.session import SessionLocal
from ..models.documents import RawItem, IngestionJob
from ..utils.settings import ALPHAVANTAGE_API_KEY

BASE = "https://www.alphavantage.co/query"

def fetch_daily(symbol: str = "AAPL") -> dict:
    db = SessionLocal()
    job = IngestionJob(name=f"alphavantage_daily_{symbol}", status="running")
    db.add(job); db.commit(); db.refresh(job)

    try:
        params = {"function":"TIME_SERIES_DAILY","symbol":symbol,"apikey":ALPHAVANTAGE_API_KEY}
        resp = requests.get(BASE, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        series = payload.get("Time Series (Daily)", {}) or payload.get("Time Series (Daily Adjusted)", {})
        if not series:
            raise RuntimeError(f"No series for {symbol}: {payload}")

        inserted, skipped = 0, 0
        for day, data in series.items():
            external_id = f"{symbol}:{day}"
            item = RawItem(
                source="alphavantage",
                external_id=external_id,
                title=f"{symbol} daily {day}",
                url=None,
                published_at=datetime.fromisoformat(day),
                content_text=None,
                raw_json={"symbol":symbol, "date":day, "data":data}
            )
            db.add(item)
            try:
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1

        job.status = "success"
        job.detail = f"alphavantage {symbol} inserted={inserted}, skipped={skipped}"
        db.commit()
        return {"inserted": inserted, "skipped": skipped}
    except Exception as e:
        db.rollback()
        job.status = "failure"
        job.detail = str(e)
        db.commit()
        return {"error": str(e)}
    finally:
        db.close()