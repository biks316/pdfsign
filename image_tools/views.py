from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render
from pathlib import Path

from .forms import (
    CompressImageForm,
    ConvertImageForm,
    CropImageForm,
    ImageToPDFForm,
    SimpleImageUploadForm,
)
from .services import (
    ImageToolError,
    compress_image,
    convert_image,
    create_crop_preview,
    create_resize_preview,
    create_enhancement_preview,
    crop_image_from_path,
    image_to_pdf,
    remove_background_placeholder,
    resize_image_from_path,
)


RELATED_IMAGE_TOOLS = [
    {'name': 'Image to PDF', 'url_name': 'image_tools:image_to_pdf'},
    {'name': 'Resize Image', 'url_name': 'image_tools:resize_image'},
    {'name': 'Compress Image', 'url_name': 'image_tools:compress_image'},
    {'name': 'Crop Image', 'url_name': 'image_tools:crop_image'},
    {'name': 'Convert Image', 'url_name': 'image_tools:convert_image'},
]


def index_view(request):
    return render(
        request,
        'image_tools/index.html',
        {
            'page_title': 'Image Tools | Convert, Resize, Compress',
            'meta_description': 'Convert images to PDF, resize, crop, and optimize PNG/JPG/WEBP files online.',
            'canonical_path': '/image-tools/',
        },
    )


def _serve_download(path, filename):
    return FileResponse(path.open('rb'), as_attachment=True, filename=filename)


def _load_processed_file(name: str) -> Path:
    raw_name = (name or '').strip()
    safe_name = Path(raw_name).name
    if not raw_name or safe_name != raw_name:
        raise ImageToolError('Invalid download token.')
    file_path = settings.MEDIA_PROCESSED_ROOT / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise ImageToolError('Preview expired. Please upload again.')
    return file_path


def image_to_pdf_view(request):
    form = ImageToPDFForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            output_path = image_to_pdf(form.cleaned_data['images'])
        except ImageToolError as exc:
            return render(request, 'image_tools/image_to_pdf.html', {'form': form, 'error_message': str(exc)})
        return _serve_download(output_path, 'images-to-pdf.pdf')

    return render(request, 'image_tools/image_to_pdf.html', {
        'form': form,
        'page_title': 'Image to PDF Converter',
        'meta_description': 'Combine one or more images into a single PDF file quickly.',
        'canonical_path': '/image-tools/image-to-pdf/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })


def resize_image_view(request):
    form = SimpleImageUploadForm()
    form.fields['image'].required = False
    preview_original_url = None
    preview_resized_url = None
    original_name = None
    resized_name = None
    selected_width = None
    selected_height = None
    action = request.POST.get('action')
    raw_left = (request.POST.get('left') or '').strip()
    raw_top = (request.POST.get('top') or '').strip()
    raw_right = (request.POST.get('right') or '').strip()
    raw_bottom = (request.POST.get('bottom') or '').strip()

    if request.method == 'POST' and action == 'download':
        try:
            raw_width = (request.POST.get('width') or '').strip()
            raw_height = (request.POST.get('height') or '').strip()
            original_name = (request.POST.get('original_name') or '').strip()
            if raw_left and raw_top and raw_right and raw_bottom and original_name:
                left = int(raw_left)
                top = int(raw_top)
                right = int(raw_right)
                bottom = int(raw_bottom)
                source_path = _load_processed_file(original_name)
                output_path = crop_image_from_path(source_path, left, top, right, bottom)
            elif raw_width and raw_height and original_name:
                width = int(raw_width)
                height = int(raw_height)
                if not (16 <= width <= 6000 and 16 <= height <= 6000):
                    raise ImageToolError('Width and height must be between 16 and 6000 pixels.')
                source_path = _load_processed_file(original_name)
                output_path = resize_image_from_path(source_path, width, height)
            else:
                output_path = _load_processed_file(request.POST.get('resized_name', ''))
        except ImageToolError as exc:
            return render(request, 'image_tools/resize_image.html', {'form': form, 'error_message': str(exc)})
        except (TypeError, ValueError):
            return render(request, 'image_tools/resize_image.html', {'form': form, 'error_message': 'Choose a valid resize area first.'})
        extension = output_path.suffix.lower() or '.jpg'
        return _serve_download(output_path, f'resized-image{extension}')

    if request.method == 'POST':
        image = request.FILES.get('image')
        raw_width = (request.POST.get('width') or '').strip()
        raw_height = (request.POST.get('height') or '').strip()
        original_name = (request.POST.get('original_name') or '').strip()
        selected_width = raw_width
        selected_height = raw_height

        try:
            width = int(raw_width)
            height = int(raw_height)
        except (TypeError, ValueError):
            return render(
                request,
                'image_tools/resize_image.html',
                {
                    'form': form,
                    'error_message': 'Choose the resize area to set width and height first.',
                    'selected_width': selected_width,
                    'selected_height': selected_height,
                },
            )

        if not (16 <= width <= 6000 and 16 <= height <= 6000):
            return render(
                request,
                'image_tools/resize_image.html',
                {
                    'form': form,
                    'error_message': 'Width and height must be between 16 and 6000 pixels.',
                    'selected_width': selected_width,
                    'selected_height': selected_height,
                },
            )

        try:
            if image:
                form = SimpleImageUploadForm(request.POST, request.FILES)
                form.fields['image'].required = False
                if not form.is_valid():
                    return render(
                        request,
                        'image_tools/resize_image.html',
                        {
                            'form': form,
                            'selected_width': selected_width,
                            'selected_height': selected_height,
                        },
                    )
                if raw_left and raw_top and raw_right and raw_bottom:
                    left = int(raw_left)
                    top = int(raw_top)
                    right = int(raw_right)
                    bottom = int(raw_bottom)
                    output_original_path, output_resized_path = create_crop_preview(
                        form.cleaned_data['image'], left, top, right, bottom
                    )
                else:
                    output_original_path, output_resized_path = create_resize_preview(
                        form.cleaned_data['image'], width, height
                    )
            else:
                if not original_name:
                    raise ImageToolError('Upload an image first.')
                output_original_path = _load_processed_file(original_name)
                if raw_left and raw_top and raw_right and raw_bottom:
                    left = int(raw_left)
                    top = int(raw_top)
                    right = int(raw_right)
                    bottom = int(raw_bottom)
                    output_resized_path = crop_image_from_path(output_original_path, left, top, right, bottom)
                else:
                    output_resized_path = resize_image_from_path(output_original_path, width, height)
            preview_original_url = f"{settings.MEDIA_URL}processed/{output_original_path.name}"
            preview_resized_url = f"{settings.MEDIA_URL}processed/{output_resized_path.name}"
            original_name = output_original_path.name
            resized_name = output_resized_path.name
        except ImageToolError as exc:
            return render(request, 'image_tools/resize_image.html', {'form': form, 'error_message': str(exc)})

    return render(request, 'image_tools/resize_image.html', {
        'form': form,
        'preview_original_url': preview_original_url,
        'preview_resized_url': preview_resized_url,
        'original_name': original_name,
        'resized_name': resized_name,
        'selected_width': selected_width,
        'selected_height': selected_height,
        'page_title': 'Resize Image Online',
        'meta_description': 'Resize PNG, JPG, or WEBP images to exact dimensions without extra software.',
        'canonical_path': '/image-tools/resize-image/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })


def compress_image_view(request):
    form = CompressImageForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            output_path = compress_image(form.cleaned_data['image'], form.cleaned_data['quality'])
        except ImageToolError as exc:
            return render(request, 'image_tools/compress_image.html', {'form': form, 'error_message': str(exc)})
        return _serve_download(output_path, 'compressed-image.jpg')

    return render(request, 'image_tools/compress_image.html', {
        'form': form,
        'page_title': 'Compress Image Online',
        'meta_description': 'Reduce image file size for faster sharing and web performance.',
        'canonical_path': '/image-tools/compress-image/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })


def crop_image_view(request):
    form = CropImageForm()
    form.fields['image'].required = False
    preview_original_url = None
    preview_cropped_url = None
    original_name = None
    cropped_name = None
    selected_left = None
    selected_top = None
    selected_right = None
    selected_bottom = None
    action = request.POST.get('action')

    if request.method == 'POST' and action == 'download':
        try:
            output_path = _load_processed_file(request.POST.get('cropped_name', ''))
        except ImageToolError as exc:
            return render(request, 'image_tools/crop_image.html', {'form': form, 'error_message': str(exc)})
        extension = output_path.suffix.lower() or '.jpg'
        return _serve_download(output_path, f'cropped-image{extension}')

    if request.method == 'POST':
        image = request.FILES.get('image')
        original_name = (request.POST.get('original_name') or '').strip()
        raw_left = (request.POST.get('left') or '').strip()
        raw_top = (request.POST.get('top') or '').strip()
        raw_right = (request.POST.get('right') or '').strip()
        raw_bottom = (request.POST.get('bottom') or '').strip()
        selected_left = raw_left
        selected_top = raw_top
        selected_right = raw_right
        selected_bottom = raw_bottom

        try:
            left = int(raw_left)
            top = int(raw_top)
            right = int(raw_right)
            bottom = int(raw_bottom)
        except (TypeError, ValueError):
            return render(
                request,
                'image_tools/crop_image.html',
                {
                    'form': form,
                    'error_message': 'Select a square crop area first.',
                    'selected_left': selected_left,
                    'selected_top': selected_top,
                    'selected_right': selected_right,
                    'selected_bottom': selected_bottom,
                },
            )

        if min(left, top, right, bottom) < 0:
            return render(
                request,
                'image_tools/crop_image.html',
                {
                    'form': form,
                    'error_message': 'Crop coordinates cannot be negative.',
                    'selected_left': selected_left,
                    'selected_top': selected_top,
                    'selected_right': selected_right,
                    'selected_bottom': selected_bottom,
                },
            )

        try:
            if image:
                form = CropImageForm(request.POST, request.FILES)
                form.fields['image'].required = False
                if not form.is_valid():
                    return render(
                        request,
                        'image_tools/crop_image.html',
                        {
                            'form': form,
                            'selected_left': selected_left,
                            'selected_top': selected_top,
                            'selected_right': selected_right,
                            'selected_bottom': selected_bottom,
                        },
                    )
                output_original_path, output_cropped_path = create_crop_preview(
                    form.cleaned_data['image'],
                    left,
                    top,
                    right,
                    bottom,
                )
            else:
                if not original_name:
                    raise ImageToolError('Upload an image first.')
                output_original_path = _load_processed_file(original_name)
                output_cropped_path = crop_image_from_path(output_original_path, left, top, right, bottom)
            preview_original_url = f"{settings.MEDIA_URL}processed/{output_original_path.name}"
            preview_cropped_url = f"{settings.MEDIA_URL}processed/{output_cropped_path.name}"
            original_name = output_original_path.name
            cropped_name = output_cropped_path.name
        except ImageToolError as exc:
            return render(request, 'image_tools/crop_image.html', {'form': form, 'error_message': str(exc)})

    return render(request, 'image_tools/crop_image.html', {
        'form': form,
        'preview_original_url': preview_original_url,
        'preview_cropped_url': preview_cropped_url,
        'original_name': original_name,
        'cropped_name': cropped_name,
        'selected_left': selected_left,
        'selected_top': selected_top,
        'selected_right': selected_right,
        'selected_bottom': selected_bottom,
        'page_title': 'Crop Image Online',
        'meta_description': 'Crop photos and screenshots with a mouse-driven selection box.',
        'canonical_path': '/image-tools/crop-image/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })


def convert_image_view(request):
    form = ConvertImageForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            output_path = convert_image(form.cleaned_data['image'], form.cleaned_data['target_format'])
        except ImageToolError as exc:
            return render(request, 'image_tools/convert_image.html', {'form': form, 'error_message': str(exc)})
        ext = form.cleaned_data['target_format'].lower().replace('jpeg', 'jpg')
        return _serve_download(output_path, f'converted-image.{ext}')

    return render(request, 'image_tools/convert_image.html', {
        'form': form,
        'page_title': 'Convert PNG JPG WEBP',
        'meta_description': 'Convert between PNG, JPG, and WEBP image formats online.',
        'canonical_path': '/image-tools/convert-image/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })


def remove_background_view(request):
    form = SimpleImageUploadForm(request.POST or None, request.FILES or None)
    placeholder_message = None
    if request.method == 'POST' and form.is_valid():
        try:
            output_path = remove_background_placeholder(form.cleaned_data['image'])
            placeholder_message = 'Placeholder background removal executed. Wire a real provider for production quality cutouts.'
            response = _serve_download(output_path, 'background-removed-placeholder.png')
            response['X-Placeholder-Notice'] = placeholder_message
            return response
        except ImageToolError as exc:
            return render(request, 'image_tools/remove_background.html', {'form': form, 'error_message': str(exc)})

    return render(request, 'image_tools/remove_background.html', {
        'form': form,
        'page_title': 'Remove Background (Placeholder Design)',
        'meta_description': 'Background removal interface with provider abstraction ready for future integration.',
        'canonical_path': '/image-tools/remove-background/',
        'placeholder_message': placeholder_message,
    })


def enhance_document_view(request):
    form = SimpleImageUploadForm(request.POST or None, request.FILES or None)
    preview_original_url = None
    preview_enhanced_url = None
    enhanced_name = None
    action = request.POST.get('action')
    if request.method == 'POST' and form.is_valid():
        try:
            if action == 'download':
                enhanced_name = request.POST.get('enhanced_name', '')
                output_path = _load_processed_file(enhanced_name)
                return _serve_download(output_path, 'enhanced-document.jpg')
            original_path, enhanced_path = create_enhancement_preview(form.cleaned_data['image'])
            preview_original_url = f"{settings.MEDIA_URL}processed/{original_path.name}"
            preview_enhanced_url = f"{settings.MEDIA_URL}processed/{enhanced_path.name}"
            enhanced_name = enhanced_path.name
        except ImageToolError as exc:
            return render(request, 'image_tools/enhance_document.html', {'form': form, 'error_message': str(exc)})
    elif request.method == 'POST' and action == 'download':
        try:
            output_path = _load_processed_file(request.POST.get('enhanced_name', ''))
        except ImageToolError as exc:
            return render(request, 'image_tools/enhance_document.html', {'form': SimpleImageUploadForm(), 'error_message': str(exc)})
        return _serve_download(output_path, 'enhanced-document.jpg')

    return render(request, 'image_tools/enhance_document.html', {
        'form': form,
        'preview_original_url': preview_original_url,
        'preview_enhanced_url': preview_enhanced_url,
        'enhanced_name': enhanced_name,
        'page_title': 'Enhance Scanned Document',
        'meta_description': 'Clean and sharpen document photos for better readability and sharing.',
        'canonical_path': '/image-tools/enhance-document/',
        'related_tools': RELATED_IMAGE_TOOLS,
    })
