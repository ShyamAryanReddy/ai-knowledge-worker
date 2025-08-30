from typing import Literal
from sqlalchemy.exc import IntegrityError
from ..db.session import SessionLocal
from ..models.documents import RawItem, IngestionJob
from datetime import datetime
import pandas as pd
from pypdf import PdfReader

def _pdf_to_text(data: bytes) -> str:
    from io import BytesIO
    reader = PdfReader(BytesIO(data))
    out = []
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out).strip()

def _csv_to_text(data: bytes) -> str:
    from io import BytesIO
    df = pd.read_csv(BytesIO(data))
    return df.to_csv(index=False)

def save_upload(filename: str, content: bytes, kind: Literal["pdf","csv","txt","other"]="other") -> dict:
    db = SessionLocal()
    job = IngestionJob(name=f"upload_{filename}", status="running")
    db.add(job); db.commit(); db.refresh(job)

    try:
        if kind == "pdf":
            text = _pdf_to_text(content)
        elif kind == "csv":
            text = _csv_to_text(content)
        elif kind == "txt":
            text = content.decode("utf-8", errors="ignore")
        else:
            text = None

        item = RawItem(
            source="upload",
            external_id=filename,
            title=filename,
            url=None,
            published_at=datetime.utcnow(),
            content_text=text,
            raw_json={"filename": filename, "bytes": len(content)}
        )
        db.add(item)
        try:
            db.commit()
            job.status = "success"; job.detail = "uploaded 1 item"; db.commit()
            return {"status":"uploaded","filename":filename}
        except IntegrityError:
            db.rollback()
            job.status = "success"; job.detail = "duplicate ignored"; db.commit()
            return {"status":"duplicate","filename":filename}
    except Exception as e:
        db.rollback()
        job.status = "failure"; job.detail = str(e); db.commit()
        return {"error": str(e)}
    finally:
        db.close()