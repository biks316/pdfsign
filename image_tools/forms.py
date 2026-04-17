from django import forms

ALLOWED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')


def _validate_image(uploaded_file):
    name = uploaded_file.name.lower()
    if not name.endswith(ALLOWED_IMAGE_EXTENSIONS):
        raise forms.ValidationError('Only PNG, JPG, JPEG, and WEBP are supported.')
    return uploaded_file


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class ImageToPDFForm(forms.Form):
    images = MultipleFileField()

    def clean_images(self):
        files = self.cleaned_data['images']
        if not files:
            raise forms.ValidationError('Upload one or more images.')
        for image in files:
            _validate_image(image)
        return files


class ResizeImageForm(forms.Form):
    image = forms.FileField()
    width = forms.IntegerField(min_value=16, max_value=6000)
    height = forms.IntegerField(min_value=16, max_value=6000)

    def clean_image(self):
        return _validate_image(self.cleaned_data['image'])


class CompressImageForm(forms.Form):
    image = forms.FileField()
    quality = forms.IntegerField(min_value=15, max_value=95, initial=70)

    def clean_image(self):
        return _validate_image(self.cleaned_data['image'])


class CropImageForm(forms.Form):
    image = forms.FileField()
    left = forms.IntegerField(min_value=0)
    top = forms.IntegerField(min_value=0)
    right = forms.IntegerField(min_value=1)
    bottom = forms.IntegerField(min_value=1)

    def clean_image(self):
        return _validate_image(self.cleaned_data['image'])


class ConvertImageForm(forms.Form):
    image = forms.FileField()
    target_format = forms.ChoiceField(choices=[('PNG', 'PNG'), ('JPEG', 'JPG'), ('WEBP', 'WEBP')])

    def clean_image(self):
        return _validate_image(self.cleaned_data['image'])


class SimpleImageUploadForm(forms.Form):
    image = forms.FileField()

    def clean_image(self):
        return _validate_image(self.cleaned_data['image'])
