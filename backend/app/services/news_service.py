import requests
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from ..db.session import SessionLocal
from ..models.documents import RawItem, IngestionJob
from ..utils.settings import NEWSAPI_KEY

NEWS_URL = "https://newsapi.org/v2/top-headlines"

def fetch_top_headlines(country: str = "us", q: str | None = None) -> dict:
    db = SessionLocal()
    job = IngestionJob(name="news_top_headlines", status="running")
    db.add(job); db.commit(); db.refresh(job)

    try:
        params = {"apiKey": NEWSAPI_KEY, "country": country}
        if q: params["q"] = q
        resp = requests.get(NEWS_URL, params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        inserted, skipped = 0, 0
        for a in payload.get("articles", []):
            url = a.get("url")
            title = a.get("title")
            published_at = a.get("publishedAt")
            content = (a.get("content") or "") + "\n" + (a.get("description") or "")

            item = RawItem(
                source="newsapi",
                external_id=url,  # dedupe by URL
                title=title,
                url=url,
                published_at=datetime.fromisoformat(published_at.replace("Z","+00:00")) if published_at else None,
                content_text=content.strip(),
                raw_json=a
            )
            db.add(item)
            try:
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1

        job.status = "success"
        job.detail = f"newsapi inserted={inserted}, skipped={skipped}"
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