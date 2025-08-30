import hashlib

def content_hash(*parts: str) -> str:
    m = hashlib.sha256()
    for p in parts:
        if p:
            m.update(p.encode("utf-8"))
    return m.hexdigest()