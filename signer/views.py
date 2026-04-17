import base64
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import fitz
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from .forms import SignPDFForm, UploadPDFForm


def _ensure_media_dirs():
    settings.MEDIA_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_SIGNED_ROOT.mkdir(parents=True, exist_ok=True)


def _pdf_path(file_id: str) -> Path:
    return settings.MEDIA_TEMP_ROOT / f'{file_id}.pdf'


def upload_pdf_view(request):
    _ensure_media_dirs()
    error_message = None

    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['pdf_file']
            file_id = uuid4().hex
            destination = _pdf_path(file_id)
            with destination.open('wb+') as out_file:
                for chunk in uploaded_file.chunks():
                    out_file.write(chunk)
            return redirect('signer:sign', file_id=file_id)
        error_message = 'Please upload a valid PDF file.'
    else:
        form = UploadPDFForm()

    return render(
        request,
        'signer/upload.html',
        {
            'form': form,
            'error_message': error_message,
        },
    )


def sign_pdf_view(request, file_id):
    _ensure_media_dirs()
    input_pdf_path = _pdf_path(file_id)
    if not input_pdf_path.exists():
        raise Http404('PDF not found. Please upload again.')

    if request.method == 'GET':
        return render(
            request,
            'signer/sign.html',
            {
                'file_id': file_id,
                'pdf_url': f"{settings.MEDIA_URL}temp/{file_id}.pdf",
            },
        )

    form = SignPDFForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            'signer/sign.html',
            {
                'file_id': file_id,
                'pdf_url': f"{settings.MEDIA_URL}temp/{file_id}.pdf",
                'error_message': 'Invalid signing data. Please try again.',
            },
            status=400,
        )

    doc = None
    try:
        placements = json.loads(form.cleaned_data['placements_json'])
        if not isinstance(placements, list) or not placements:
            raise ValueError('At least one placement is required.')
        if len(placements) > 100:
            raise ValueError('Too many placements.')

        add_date = form.cleaned_data['add_date']

        doc = fitz.open(input_pdf_path)
        for placement in placements:
            if not isinstance(placement, dict):
                raise ValueError('Invalid placement payload.')

            signature_data = placement.get('signature_data', '')
            if not isinstance(signature_data, str) or not signature_data.startswith('data:image/png;base64,'):
                raise ValueError('Invalid signature format.')

            _, image_data = signature_data.split(',', 1)
            signature_bytes = base64.b64decode(image_data)
            if not signature_bytes:
                raise ValueError('Empty signature image.')

            page_number = int(placement.get('page_number'))
            x_ratio = float(placement.get('x_ratio'))
            y_ratio = float(placement.get('y_ratio'))

            if page_number < 1 or page_number > doc.page_count:
                raise ValueError('Invalid page selected.')
            if not (0 <= x_ratio <= 1) or not (0 <= y_ratio <= 1):
                raise ValueError('Invalid coordinates.')

            page = doc[page_number - 1]
            page_rect = page.rect

            signature_pixmap = fitz.Pixmap(signature_bytes)
            if signature_pixmap.width <= 0 or signature_pixmap.height <= 0:
                raise ValueError('Invalid signature dimensions.')
            aspect_ratio = signature_pixmap.width / signature_pixmap.height

            sig_width = max(120, page_rect.width * 0.24)
            sig_height = sig_width / max(aspect_ratio, 0.1)
            max_sig_height = page_rect.height * 0.16
            if sig_height > max_sig_height:
                sig_height = max_sig_height
                sig_width = sig_height * aspect_ratio

            x = page_rect.width * x_ratio
            y = page_rect.height * y_ratio

            # Keep signature within page boundaries while preserving click-based placement.
            x = min(max(0, x), max(0, page_rect.width - sig_width))
            y = min(max(0, y), max(0, page_rect.height - sig_height))

            sig_rect = fitz.Rect(x, y, x + sig_width, y + sig_height)
            page.insert_image(sig_rect, stream=signature_bytes, keep_proportion=True, overlay=True)

            if add_date:
                date_text = datetime.now().strftime('%Y-%m-%d')
                # Date is anchored at the exact click position when enabled.
                date_x = min(max(0, page_rect.width * x_ratio), page_rect.width - 95)
                date_y = min(max(12, page_rect.height * y_ratio), page_rect.height - 10)
                date_point = fitz.Point(date_x, date_y)
                page.insert_text(date_point, date_text, fontsize=11, color=(0, 0, 0))

        output_id = uuid4().hex
        output_path = settings.MEDIA_SIGNED_ROOT / f'{output_id}_signed.pdf'
        doc.save(output_path)

        return FileResponse(
            output_path.open('rb'),
            as_attachment=True,
            filename='signed.pdf',
            content_type='application/pdf',
        )
    except Exception:
        return render(
            request,
            'signer/sign.html',
            {
                'file_id': file_id,
                'pdf_url': f"{settings.MEDIA_URL}temp/{file_id}.pdf",
                'error_message': 'Failed to sign PDF. Please try again.',
            },
            status=400,
        )
    finally:
        if doc is not None:
            doc.close()
