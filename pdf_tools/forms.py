from django import forms


class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(label='PDF file')

    def clean_pdf_file(self):
        uploaded_file = self.cleaned_data['pdf_file']
        if not uploaded_file.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Only PDF files are allowed.')

        header = uploaded_file.read(4)
        uploaded_file.seek(0)
        if header != b'%PDF':
            raise forms.ValidationError('Invalid PDF header.')

        return uploaded_file


class SignPDFApplyForm(forms.Form):
    placements_json = forms.CharField()


class AddDateApplyForm(forms.Form):
    page_number = forms.IntegerField(min_value=1)
    x_ratio = forms.FloatField(min_value=0, max_value=1)
    y_ratio = forms.FloatField(min_value=0, max_value=1)
    date_text = forms.CharField(required=False, max_length=40)
