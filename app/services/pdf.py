from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from flask import current_app, render_template
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def _link_callback(uri: str, rel: str) -> str:
    if uri.startswith("/"):
        uri = uri[1:]
    static_url_path = current_app.static_url_path.lstrip("/")
    if uri.startswith(static_url_path + "/"):
        path = uri[len(static_url_path) + 1 :]
        return str(Path(current_app.static_folder) / path)
    return uri


def render_pdf_bytes(template_name: str, context: dict[str, Any]) -> io.BytesIO:
    try:
        from xhtml2pdf import pisa
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "PDF 依赖未就绪：请先执行 `pip install -r requirements.txt`（或升级 xhtml2pdf）。"
        ) from e

    # Register a CJK-capable built-in CID font for Chinese text rendering in PDF.
    # This avoids "blank PDF" symptoms on machines without an embedded Chinese TTF.
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass

    html = render_template(template_name, **context)
    pdf = io.BytesIO()
    result = pisa.CreatePDF(html, dest=pdf, link_callback=_link_callback, encoding="utf-8")
    if result.err:
        raise RuntimeError("PDF rendering failed")
    pdf.seek(0)
    return pdf
