import base64
from pathlib import Path

import jdatetime
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.urls import URLFetcher


def document_pdf(doc):
    font = base64.b64encode((Path(__file__).parent / "fonts/Vazirmatn.woff2").read_bytes()).decode(
        "ascii"
    )
    html = render_to_string(
        "documents/document.html",
        {
            "doc": doc,
            "lines": doc.lines.select_related("product").all(),
            "jalali_date": jdatetime.date.fromgregorian(date=doc.doc_date).strftime("%Y/%m/%d"),
            "font_data": font,
        },
    )

    fetcher = URLFetcher(allowed_protocols=["data"], allow_redirects=False, fail_on_errors=True)
    return HTML(string=html, url_fetcher=fetcher).write_pdf()
