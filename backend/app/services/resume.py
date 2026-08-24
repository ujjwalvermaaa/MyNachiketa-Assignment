import io
import re

import pymupdf as fitz
import httpx


DRIVE_ID_RE = re.compile(r"/file/d/([a-zA-Z0-9_-]+)")
DRIVE_ID_Q_RE = re.compile(r"[?&]id=([a-zA-Z0-9_-]+)")


def extract_drive_id(url: str) -> str:
    match = DRIVE_ID_RE.search(url or "")
    if match:
        return match.group(1)
    match = DRIVE_ID_Q_RE.search(url or "")
    return match.group(1) if match else ""


def extract_pdf_text(data: bytes) -> str:
    doc = fitz.open(stream=io.BytesIO(data), filetype="pdf")
    parts = []
    try:
        for page in doc:
            parts.append(page.get_text("text") or "")
    finally:
        doc.close()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()


def _confirm_url(html: str, file_id: str) -> str | None:
    match = re.search(r"confirm=([0-9A-Za-z_]+)", html)
    if not match:
        return None
    return (
        f"https://drive.google.com/uc?export=download&confirm={match.group(1)}&id={file_id}"
    )


def download_resume(url: str, timeout: float = 30) -> str:
    if not url or str(url).strip() in {"nan", "None", "-"}:
        raise ValueError("Missing resume link")

    url = str(url).strip()
    file_id = extract_drive_id(url)
    candidates = []
    if file_id:
        candidates.append(f"https://drive.google.com/uc?export=download&id={file_id}")
    candidates.append(url)

    last_error = "Could not download resume"
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": "myNachiketa/1.0"}) as client:
        for target in candidates:
            response = client.get(target)
            content_type = response.headers.get("content-type", "")
            data = response.content
            if data[:4] == b"%PDF" or "pdf" in content_type.lower():
                return extract_pdf_text(data)
            if file_id and b"<html" in data[:200].lower():
                confirm = _confirm_url(data.decode("utf-8", "replace"), file_id)
                if confirm:
                    retry = client.get(confirm)
                    if retry.content[:4] == b"%PDF":
                        return extract_pdf_text(retry.content)
            last_error = f"Resume is not a PDF (content-type={content_type})"
    raise ValueError(last_error)
