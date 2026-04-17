from django import forms


class UploadPDFForm(forms.Form):
    pdf_file = forms.FileField(label='PDF file')

    def clean_pdf_file(self):
        uploaded_file = self.cleaned_data['pdf_file']
        filename = uploaded_file.name.lower()
        if not filename.endswith('.pdf'):
            raise forms.ValidationError('Only .pdf files are allowed.')

        header = uploaded_file.read(4)
        uploaded_file.seek(0)
        if header != b'%PDF':
            raise forms.ValidationError('Invalid PDF file.')

        return uploaded_file


class SignPDFForm(forms.Form):
    placements_json = forms.CharField()
    add_date = forms.BooleanField(required=False)
