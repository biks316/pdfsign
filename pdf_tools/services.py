import base64
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import fitz
from django.conf import settings


class PDFToolError(ValueError):
    pass


def ensure_media_dirs():
    settings.MEDIA_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_SIGNED_ROOT.mkdir(parents=True, exist_ok=True)


def save_uploaded_pdf(uploaded_file) -> str:
    ensure_media_dirs()
    file_id = uuid4().hex
    destination = settings.MEDIA_TEMP_ROOT / f'{file_id}.pdf'
    with destination.open('wb+') as out_file:
        for chunk in uploaded_file.chunks():
            out_file.write(chunk)
    return file_id


def get_temp_pdf_path(file_id: str) -> Path:
    return settings.MEDIA_TEMP_ROOT / f'{file_id}.pdf'


def build_temp_pdf_url(file_id: str) -> str:
    return f"{settings.MEDIA_URL}temp/{file_id}.pdf"


def _decode_signature(data_url: str) -> bytes:
    if not data_url or not data_url.startswith('data:image/'):
        raise PDFToolError('Signature must be a valid image data URL.')
    try:
        _, encoded = data_url.split(',', 1)
        signature_bytes = base64.b64decode(encoded)
    except Exception as exc:
        raise PDFToolError('Failed to parse signature image.') from exc
    if not signature_bytes:
        raise PDFToolError('Signature image is empty.')
    return signature_bytes


def _safe_float(value, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise PDFToolError(f'Invalid {field_name}.') from exc
    return parsed


def _safe_int(value, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PDFToolError(f'Invalid {field_name}.') from exc
    return parsed


def process_sign_pdf(input_path: Path, placements_json: str) -> Path:
    try:
        placements = json.loads(placements_json)
    except json.JSONDecodeError as exc:
        raise PDFToolError('Invalid placement payload.') from exc

    if not isinstance(placements, list) or not placements:
        raise PDFToolError('At least one placement is required.')
    if len(placements) > 100:
        raise PDFToolError('Too many placements.')

    doc = fitz.open(input_path)
    try:
        for placement in placements:
            if not isinstance(placement, dict):
                raise PDFToolError('Placement entry is invalid.')

            include_signature = bool(placement.get('include_signature', True))
            include_date = bool(placement.get('include_date', False))
            if not include_signature and not include_date:
                raise PDFToolError('Each placement must include signature, date, or both.')

            page_number = _safe_int(placement.get('page_number'), 'page number')
            if page_number < 1 or page_number > doc.page_count:
                raise PDFToolError('Page number is out of range.')

            x_ratio = _safe_float(placement.get('x_ratio'), 'x ratio')
            y_ratio = _safe_float(placement.get('y_ratio'), 'y ratio')
            if not (0 <= x_ratio <= 1 and 0 <= y_ratio <= 1):
                raise PDFToolError('Placement coordinates are out of range.')

            width_ratio_raw = placement.get('width_ratio')
            height_ratio_raw = placement.get('height_ratio')
            width_ratio = None if width_ratio_raw is None else _safe_float(width_ratio_raw, 'width ratio')
            height_ratio = None if height_ratio_raw is None else _safe_float(height_ratio_raw, 'height ratio')
            if width_ratio is not None and not (0 < width_ratio <= 1):
                raise PDFToolError('Width ratio is out of range.')
            if height_ratio is not None and not (0 < height_ratio <= 1):
                raise PDFToolError('Height ratio is out of range.')

            page = doc[page_number - 1]
            rect = page.rect
            x = rect.width * x_ratio
            y = rect.height * y_ratio

            if include_signature:
                signature_bytes = _decode_signature(placement.get('signature_data', ''))
                pixmap = fitz.Pixmap(signature_bytes)
                aspect_ratio = max(0.1, pixmap.width / max(1, pixmap.height))

                if width_ratio is not None:
                    sig_width = rect.width * width_ratio
                    sig_height = sig_width / aspect_ratio
                elif height_ratio is not None:
                    sig_height = rect.height * height_ratio
                    sig_width = sig_height * aspect_ratio
                else:
                    sig_width = max(120, rect.width * 0.24)
                    sig_height = sig_width / aspect_ratio

                min_sig_width = max(36, rect.width * 0.06)
                sig_width = min(max(sig_width, min_sig_width), rect.width)
                sig_height = sig_width / aspect_ratio
                has_custom_size = width_ratio is not None or height_ratio is not None
                max_sig_height = rect.height if has_custom_size else rect.height * 0.16
                if sig_height > max_sig_height:
                    sig_height = max_sig_height
                    sig_width = sig_height * aspect_ratio

                x = min(max(0, x), max(0, rect.width - sig_width))
                y = min(max(0, y), max(0, rect.height - sig_height))
                sig_rect = fitz.Rect(x, y, x + sig_width, y + sig_height)
                page.insert_image(sig_rect, stream=signature_bytes, keep_proportion=True, overlay=True)

            if include_date:
                today_text = date.today().isoformat()
                fontsize = 11
                try:
                    date_width = fitz.get_text_length(today_text, fontsize=fontsize)
                except Exception:
                    date_width = 72

                date_x = min(max(0, x), max(0, rect.width - date_width))
                date_y = min(max(fontsize + 1, y + fontsize + 6), rect.height - 2)
                page.insert_text(
                    fitz.Point(date_x, date_y),
                    today_text,
                    fontsize=fontsize,
                    fontname='times-italic',
                    color=(0, 0, 0),
                )

        output_path = settings.MEDIA_SIGNED_ROOT / f"{uuid4().hex}_signed.pdf"
        doc.save(output_path)
        return output_path
    finally:
        doc.close()


def process_add_date_pdf(input_path: Path, page_number: int, x_ratio: float, y_ratio: float, date_text: str = '') -> Path:
    doc = fitz.open(input_path)
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise PDFToolError('Page number is out of range.')
        if not (0 <= x_ratio <= 1 and 0 <= y_ratio <= 1):
            raise PDFToolError('Coordinates must be between 0 and 1.')

        page = doc[page_number - 1]
        rect = page.rect

        date_label = date_text.strip() or date.today().isoformat()
        fontsize = 13
        try:
            date_width = fitz.get_text_length(date_label, fontsize=fontsize)
        except Exception:
            date_width = 100

        x = min(max(0, rect.width * x_ratio), max(0, rect.width - date_width))
        y = min(max(fontsize + 2, rect.height * y_ratio), rect.height - 4)

        page.insert_text(
            fitz.Point(x, y),
            date_label,
            fontsize=fontsize,
            fontname='helv',
            color=(0.08, 0.08, 0.08),
        )

        output_path = settings.MEDIA_SIGNED_ROOT / f"{uuid4().hex}_dated.pdf"
        doc.save(output_path)
        return output_path
    finally:
        doc.close()
