"""MCP stdio server for fetching documents from HTTP URLs.

Handles both web pages (HTML) and binary document downloads (PDF/Word/PPT/Excel),
converting them to readable Markdown text via markitdown. Embedded images are
extracted and returned as ImageContent so vision-capable models can see them.

Usage:
    python3 -m mirror_harness.mcp.doc_fetch_server
"""

from __future__ import annotations

import base64
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from markitdown import MarkItDown
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import ImageContent, TextContent, Tool

logger = logging.getLogger(__name__)

server = Server("mirrorsphere-doc-fetch")

MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_IMAGES = 15
MIN_IMAGE_SIZE = 5 * 1024  # Skip tiny images (icons, bullets) < 5KB

BINARY_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.ms-powerpoint",
    "application/vnd.ms-excel",
    "application/octet-stream",
}

BINARY_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"}

TEXT_CONTENT_TYPES = {"text/plain", "text/markdown"}


def _url_extension(url: str) -> str:
    path = urlparse(url).path
    return Path(path).suffix.lower()


def _is_binary_document(content_type: str, url: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    if ct in BINARY_CONTENT_TYPES:
        return True
    if _url_extension(url) in BINARY_EXTENSIONS:
        return True
    return False


def _is_plain_text(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return ct in TEXT_CONTENT_TYPES


def _filename_from_response(response: httpx.Response, url: str) -> str:
    cd = response.headers.get("content-disposition", "")
    if "filename=" in cd:
        parts = cd.split("filename=")
        name = parts[-1].strip().strip('"').strip("'")
        if name:
            return Path(name).name
    path = urlparse(url).path
    name = Path(path).name
    return name if name else "document"


def _convert_bytes_to_markdown(data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower() or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        md = MarkItDown()
        result = md.convert(str(tmp_path))
        text = getattr(result, "text_content", None) or getattr(result, "text", None) or str(result)
        return text
    finally:
        tmp_path.unlink(missing_ok=True)


def _convert_html_to_markdown(html: str, url: str) -> str:
    suffix = _url_extension(url) or ".html"
    if suffix not in {".html", ".htm"}:
        suffix = ".html"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, encoding="utf-8", delete=False) as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)
    try:
        md = MarkItDown()
        result = md.convert(str(tmp_path))
        text = getattr(result, "text_content", None) or getattr(result, "text", None) or str(result)
        return text
    finally:
        tmp_path.unlink(missing_ok=True)


def _extract_images_from_pdf(data: bytes) -> list[ImageContent]:
    """Extract embedded images from PDF using pymupdf. Returns empty list if unavailable."""
    try:
        import pymupdf
    except ImportError:
        return []

    images: list[ImageContent] = []
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        for page_num in range(len(doc)):
            if len(images) >= MAX_IMAGES:
                break
            page = doc[page_num]
            for img_info in page.get_images(full=True):
                if len(images) >= MAX_IMAGES:
                    break
                xref = img_info[0]
                try:
                    pix = pymupdf.Pixmap(doc, xref)
                    if pix.n > 4:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    img_bytes = pix.tobytes("png")
                    if len(img_bytes) < MIN_IMAGE_SIZE:
                        continue
                    b64 = base64.b64encode(img_bytes).decode("ascii")
                    images.append(ImageContent(
                        type="image",
                        data=b64,
                        mimeType="image/png",
                    ))
                except Exception:
                    continue
        doc.close()
    except Exception:
        logger.debug("Failed to extract images from PDF", exc_info=True)

    return images


def _extract_images_from_docx(data: bytes) -> list[ImageContent]:
    """Extract embedded images from DOCX. Returns empty list if unavailable."""
    try:
        from zipfile import ZipFile
    except ImportError:
        return []

    images: list[ImageContent] = []
    try:
        with ZipFile(io.BytesIO(data)) as zf:
            image_files = [
                n for n in zf.namelist()
                if n.startswith("word/media/") and any(n.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp"))
            ]
            for img_name in image_files[:MAX_IMAGES]:
                img_data = zf.read(img_name)
                if len(img_data) < MIN_IMAGE_SIZE:
                    continue
                ext = Path(img_name).suffix.lower()
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
                    ext.lstrip("."), "image/png"
                )
                b64 = base64.b64encode(img_data).decode("ascii")
                images.append(ImageContent(type="image", data=b64, mimeType=mime))
                if len(images) >= MAX_IMAGES:
                    break
    except Exception:
        logger.debug("Failed to extract images from DOCX", exc_info=True)

    return images


def _extract_images_from_pptx(data: bytes) -> list[ImageContent]:
    """Extract embedded images from PPTX. Returns empty list if unavailable."""
    try:
        from zipfile import ZipFile
    except ImportError:
        return []

    images: list[ImageContent] = []
    try:
        with ZipFile(io.BytesIO(data)) as zf:
            image_files = [
                n for n in zf.namelist()
                if n.startswith("ppt/media/") and any(n.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp"))
            ]
            for img_name in image_files[:MAX_IMAGES]:
                img_data = zf.read(img_name)
                if len(img_data) < MIN_IMAGE_SIZE:
                    continue
                ext = Path(img_name).suffix.lower()
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
                    ext.lstrip("."), "image/png"
                )
                b64 = base64.b64encode(img_data).decode("ascii")
                images.append(ImageContent(type="image", data=b64, mimeType=mime))
                if len(images) >= MAX_IMAGES:
                    break
    except Exception:
        logger.debug("Failed to extract images from PPTX", exc_info=True)

    return images


def _extract_images(data: bytes, filename: str) -> list[ImageContent]:
    """Extract images from a document based on its file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_images_from_pdf(data)
    if ext in {".docx", ".doc"}:
        return _extract_images_from_docx(data)
    if ext in {".pptx", ".ppt"}:
        return _extract_images_from_pptx(data)
    return []


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch-document",
            description=(
                "Download a document from an HTTP URL and convert it to readable Markdown. "
                "Supports web pages (HTML), PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), "
                "and plain text files. Embedded images in PDF/Word/PPT are automatically extracted "
                "and returned for visual inspection. Use this when a user provides a URL to a PRD, "
                "technical review document, or any requirement document."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The HTTP/HTTPS URL of the document to fetch.",
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "Request timeout in seconds (default 30).",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    if name == "fetch-document":
        return _handle_fetch_document(arguments)
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


def _handle_fetch_document(args: dict[str, Any]) -> list[TextContent | ImageContent]:
    url = args["url"]
    timeout = args.get("timeout", 30)

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return [TextContent(type="text", text=json.dumps({"error": "Only HTTP/HTTPS URLs are supported."}))]

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            head_resp = client.head(url)
            content_type = head_resp.headers.get("content-type", "")
            content_length = int(head_resp.headers.get("content-length", 0))

            if content_length > MAX_DOWNLOAD_SIZE:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"File too large ({content_length / 1024 / 1024:.1f} MB). Maximum is 50 MB.",
                }))]

            resp = client.get(url)
            resp.raise_for_status()

            if not content_type:
                content_type = resp.headers.get("content-type", "")

            filename = _filename_from_response(resp, url)

            if len(resp.content) > MAX_DOWNLOAD_SIZE:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"Downloaded content too large ({len(resp.content) / 1024 / 1024:.1f} MB). Maximum is 50 MB.",
                }))]

            images: list[ImageContent] = []

            if _is_plain_text(content_type):
                content = resp.text
            elif _is_binary_document(content_type, url):
                content = _convert_bytes_to_markdown(resp.content, filename)
                images = _extract_images(resp.content, filename)
            else:
                content = _convert_html_to_markdown(resp.text, url)

    except httpx.TimeoutException:
        return [TextContent(type="text", text=json.dumps({"error": f"Request timed out after {timeout}s."}))]
    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}"}))]
    except Exception as e:
        logger.exception("Failed to fetch document from %s", url)
        return [TextContent(type="text", text=json.dumps({"error": f"Failed to fetch document: {e}"}))]

    result = {
        "content": content,
        "source_url": url,
        "content_type": content_type.split(";")[0].strip(),
        "filename": filename,
        "images_extracted": len(images),
    }
    response: list[TextContent | ImageContent] = [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    response.extend(images)
    return response


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="mirrorsphere-doc-fetch",
            server_version="0.1.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
