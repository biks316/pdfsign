from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from .forms import AddDateApplyForm, PDFUploadForm, SignPDFApplyForm
from .services import (
    PDFToolError,
    build_temp_pdf_url,
    get_temp_pdf_path,
    process_add_date_pdf,
    process_sign_pdf,
    save_uploaded_pdf,
)


RELATED_PDF_TOOLS = [
    {'name': 'Sign PDF', 'url_name': 'pdf_tools:sign_pdf'},
    {'name': 'Add Date to PDF', 'url_name': 'pdf_tools:add_date'},
]


def pdf_tools_index_view(request):
    return render(
        request,
        'pdf_tools/index.html',
        {
            'page_title': 'PDF Tools | Sign and Stamp Documents',
            'meta_description': 'Use online PDF tools to sign documents and stamp current dates with quick browser previews.',
            'canonical_path': '/pdf-tools/',
        },
    )


def sign_pdf_view(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_id = save_uploaded_pdf(form.cleaned_data['pdf_file'])
            return redirect('pdf_tools:sign_pdf_editor', file_id=file_id)
    else:
        form = PDFUploadForm()

    return render(
        request,
        'pdf_tools/sign_upload.html',
        {
            'form': form,
            'page_title': 'Sign PDF Online | Draw or Upload Signature',
            'meta_description': 'Upload a PDF, place your signature on any page, and download the signed file instantly.',
            'canonical_path': '/pdf-tools/sign-pdf/',
            'related_tools': RELATED_PDF_TOOLS,
            'faq_schema': [
                {
                    'question': 'Can I upload a signature image instead of drawing?',
                    'answer': 'Yes. The sign tool supports both signature drawing and image upload.',
                },
                {
                    'question': 'Will the original PDF layout change?',
                    'answer': 'No. The app preserves your PDF content and only overlays signature and date elements.',
                },
            ],
        },
    )


def sign_pdf_editor_view(request, file_id: str):
    source_path = get_temp_pdf_path(file_id)
    if not source_path.exists():
        raise Http404('PDF not found. Please upload a new file.')

    if request.method == 'POST':
        form = SignPDFApplyForm(request.POST)
        if form.is_valid():
            try:
                output_path = process_sign_pdf(source_path, form.cleaned_data['placements_json'])
            except PDFToolError as exc:
                return render(
                    request,
                    'pdf_tools/sign_editor.html',
                    {
                        'file_id': file_id,
                        'pdf_url': build_temp_pdf_url(file_id),
                        'error_message': str(exc),
                    },
                    status=400,
                )
            return FileResponse(
                output_path.open('rb'),
                as_attachment=True,
                filename='signed.pdf',
                content_type='application/pdf',
            )

    return render(
        request,
        'pdf_tools/sign_editor.html',
        {
            'file_id': file_id,
            'pdf_url': build_temp_pdf_url(file_id),
            'page_title': 'Place Signature on PDF | PDFSign Studio',
            'meta_description': 'Preview your PDF and click to place signature and date before downloading.',
            'canonical_path': f'/pdf-tools/sign-pdf/editor/{file_id}/',
        },
    )


def add_date_view(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_id = save_uploaded_pdf(form.cleaned_data['pdf_file'])
            return redirect('pdf_tools:add_date_editor', file_id=file_id)
    else:
        form = PDFUploadForm()

    return render(
        request,
        'pdf_tools/add_date_upload.html',
        {
            'form': form,
            'page_title': 'Add Date to PDF Online',
            'meta_description': 'Stamp today\'s date or custom date text onto any page in your PDF.',
            'canonical_path': '/pdf-tools/add-date-to-pdf/',
            'related_tools': RELATED_PDF_TOOLS,
        },
    )


def add_date_editor_view(request, file_id: str):
    source_path = get_temp_pdf_path(file_id)
    if not source_path.exists():
        raise Http404('PDF not found. Please upload a new file.')

    if request.method == 'POST':
        form = AddDateApplyForm(request.POST)
        if form.is_valid():
            try:
                output_path = process_add_date_pdf(
                    source_path,
                    page_number=form.cleaned_data['page_number'],
                    x_ratio=form.cleaned_data['x_ratio'],
                    y_ratio=form.cleaned_data['y_ratio'],
                    date_text=form.cleaned_data['date_text'],
                )
            except PDFToolError as exc:
                return render(
                    request,
                    'pdf_tools/add_date_editor.html',
                    {
                        'file_id': file_id,
                        'pdf_url': build_temp_pdf_url(file_id),
                        'error_message': str(exc),
                        'date_text': request.POST.get('date_text', ''),
                    },
                    status=400,
                )
            return FileResponse(
                output_path.open('rb'),
                as_attachment=True,
                filename='dated.pdf',
                content_type='application/pdf',
            )

    return render(
        request,
        'pdf_tools/add_date_editor.html',
        {
            'file_id': file_id,
            'pdf_url': build_temp_pdf_url(file_id),
            'page_title': 'Place Date on PDF | PDFSign Studio',
            'meta_description': 'Click on the PDF preview to place a date stamp, then download the updated file.',
            'canonical_path': f'/pdf-tools/add-date-to-pdf/editor/{file_id}/',
            'date_text': '',
        },
    )
