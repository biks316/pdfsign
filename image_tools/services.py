from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageEnhance, ImageOps
from django.conf import settings


class ImageToolError(ValueError):
    pass


class BackgroundRemovalService:
    """Provider interface for future background-removal integrations."""

    def remove_background(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError('Connect a third-party or ML provider here.')


class PlaceholderBackgroundRemovalService(BackgroundRemovalService):
    def remove_background(self, image: Image.Image) -> Image.Image:
        # Placeholder fallback that returns the original image unchanged.
        return image


def ensure_processed_dir():
    settings.MEDIA_PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)


def _open_image(uploaded_file) -> Image.Image:
    try:
        image = Image.open(uploaded_file)
        image.load()
    except Exception as exc:
        raise ImageToolError('Unable to read image.') from exc
    return image


def _save_output(image: Image.Image, extension: str, image_format: str, **save_kwargs) -> Path:
    ensure_processed_dir()
    output_path = settings.MEDIA_PROCESSED_ROOT / f'{uuid4().hex}.{extension}'
    image.save(output_path, format=image_format, **save_kwargs)
    return output_path


def _resolve_image_format(image: Image.Image) -> tuple[str, str]:
    image_format = (image.format or 'PNG').upper()
    if image_format == 'JPG':
        image_format = 'JPEG'
    extension = 'jpg' if image_format == 'JPEG' else image_format.lower()
    return image_format, extension


def _prepare_image_for_format(image: Image.Image, image_format: str) -> Image.Image:
    if image_format == 'JPEG' and image.mode not in ('RGB', 'L'):
        return image.convert('RGB')
    return image


def image_to_pdf(images) -> Path:
    pil_images = []
    for file_obj in images:
        image = _open_image(file_obj).convert('RGB')
        pil_images.append(image)

    if not pil_images:
        raise ImageToolError('No images uploaded.')

    ensure_processed_dir()
    output_path = settings.MEDIA_PROCESSED_ROOT / f'{uuid4().hex}.pdf'
    first, rest = pil_images[0], pil_images[1:]
    first.save(output_path, save_all=True, append_images=rest)
    return output_path


def resize_image(uploaded_file, width: int, height: int) -> Path:
    image = _open_image(uploaded_file)
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    image_format, extension = _resolve_image_format(image)
    resized = _prepare_image_for_format(resized, image_format)
    return _save_output(resized, extension=extension, image_format=image_format)


def create_resize_preview(uploaded_file, width: int, height: int) -> tuple[Path, Path]:
    image = _open_image(uploaded_file)
    image_format, extension = _resolve_image_format(image)
    original = _prepare_image_for_format(image.copy(), image_format)
    resized = _prepare_image_for_format(
        image.resize((width, height), Image.Resampling.LANCZOS),
        image_format,
    )
    original_path = _save_output(original, extension=extension, image_format=image_format)
    resized_path = _save_output(resized, extension=extension, image_format=image_format)
    return original_path, resized_path


def resize_image_from_path(source_path: Path, width: int, height: int) -> Path:
    with source_path.open('rb') as source_file:
        return resize_image(source_file, width, height)


def compress_image(uploaded_file, quality: int) -> Path:
    image = _open_image(uploaded_file).convert('RGB')
    return _save_output(image, extension='jpg', image_format='JPEG', quality=quality, optimize=True)


def crop_image(uploaded_file, left: int, top: int, right: int, bottom: int) -> Path:
    image = _open_image(uploaded_file)
    return _crop_image_instance(image, left, top, right, bottom)


def _normalize_crop_box(image: Image.Image, left: int, top: int, right: int, bottom: int) -> tuple[int, int, int, int]:
    width, height = image.size
    right = min(right, width)
    bottom = min(bottom, height)
    if left >= right or top >= bottom:
        raise ImageToolError('Invalid crop dimensions.')
    return left, top, right, bottom


def _crop_image_instance(image: Image.Image, left: int, top: int, right: int, bottom: int) -> Path:
    left, top, right, bottom = _normalize_crop_box(image, left, top, right, bottom)
    cropped = image.crop((left, top, right, bottom))
    fmt = image.format or 'PNG'
    extension = 'jpg' if fmt == 'JPEG' else fmt.lower()
    return _save_output(cropped, extension=extension, image_format=fmt)


def crop_image_from_path(source_path: Path, left: int, top: int, right: int, bottom: int) -> Path:
    with source_path.open('rb') as source_file:
        return crop_image(source_file, left, top, right, bottom)


def create_crop_preview(uploaded_file, left: int, top: int, right: int, bottom: int) -> tuple[Path, Path]:
    image = _open_image(uploaded_file)
    left, top, right, bottom = _normalize_crop_box(image, left, top, right, bottom)
    image_format, extension = _resolve_image_format(image)
    original = _prepare_image_for_format(image.copy(), image_format)
    cropped_image = image.crop((left, top, right, bottom))
    cropped = _prepare_image_for_format(cropped_image, image_format)
    original_path = _save_output(original, extension=extension, image_format=image_format)
    cropped_path = _save_output(cropped, extension=extension, image_format=image_format)
    return original_path, cropped_path


def convert_image(uploaded_file, target_format: str) -> Path:
    image = _open_image(uploaded_file)
    image_format = target_format.upper()

    if image_format == 'JPEG':
        converted = image.convert('RGB')
        extension = 'jpg'
    else:
        converted = image.convert('RGBA') if image_format == 'PNG' else image.convert('RGB')
        extension = image_format.lower()

    return _save_output(converted, extension=extension, image_format=image_format)


def _enhance_document_image(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    contrast = ImageOps.autocontrast(grayscale)
    sharpened = ImageEnhance.Sharpness(contrast).enhance(2.0)
    return ImageOps.posterize(sharpened.convert('RGB'), bits=4)


def create_enhancement_preview(uploaded_file) -> tuple[Path, Path]:
    image = _open_image(uploaded_file)
    original = image.convert('RGB')
    enhanced = _enhance_document_image(image)
    original_path = _save_output(original, extension='jpg', image_format='JPEG', quality=92, optimize=True)
    enhanced_path = _save_output(enhanced, extension='jpg', image_format='JPEG', quality=90, optimize=True)
    return original_path, enhanced_path


def enhance_document(uploaded_file) -> Path:
    image = _open_image(uploaded_file)
    cleaned = _enhance_document_image(image)
    return _save_output(cleaned, extension='jpg', image_format='JPEG', quality=90, optimize=True)


def remove_background_placeholder(uploaded_file, service: BackgroundRemovalService | None = None) -> Path:
    image = _open_image(uploaded_file)
    service = service or PlaceholderBackgroundRemovalService()
    result = service.remove_background(image)
    output = BytesIO()
    result.save(output, format='PNG')
    output.seek(0)
    ensure_processed_dir()
    path = settings.MEDIA_PROCESSED_ROOT / f'{uuid4().hex}.png'
    with path.open('wb') as f:
        f.write(output.read())
    return path
