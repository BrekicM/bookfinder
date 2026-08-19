from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from book_finder.i18n.strings import LANGUAGE_LABELS, SUPPORTED_LANGUAGES, t

templates = Jinja2Templates(directory="src/book_finder/web/templates")


def _language_links(request: Request) -> dict[str, str]:
    params = dict(request.query_params)
    links = {}
    for code in SUPPORTED_LANGUAGES:
        query_string = urlencode({**params, "lang": code})
        links[code] = f"{request.url.path}?{query_string}"
    return links


def render(request: Request, template_name: str, context: dict | None = None) -> HTMLResponse:
    lang = request.state.lang
    full_context = {
        **(context or {}),
        "lang": lang,
        "t": lambda key, *args: t(key, lang, *args),
        "language_labels": LANGUAGE_LABELS,
        "language_links": _language_links(request),
    }
    return templates.TemplateResponse(request, template_name, full_context)
