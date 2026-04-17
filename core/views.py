from django.http import HttpResponse
from django.shortcuts import render


TRUST_ITEMS = [
    'Files are processed over secure HTTPS connections.',
    'Temporary uploads are isolated and never publicly listed.',
    'No heavy front-end framework. Fast pages and simple workflow.',
]


def home_view(request):
    return render(
        request,
        'core/home.html',
        {
            'trust_items': TRUST_ITEMS,
            'page_title': 'PDF and Image Tools Platform | PDFSign Studio',
            'meta_description': 'Sign PDFs, add dates, convert and optimize images with a fast and privacy-focused tool platform.',
            'canonical_path': '/',
            'og_type': 'website',
            'faq_schema': [
                {
                    'question': 'Do I need to create an account?',
                    'answer': 'Most tools can be used without an account. Accounts unlock profile and future saved workflows.',
                },
                {
                    'question': 'Can I sign PDFs online?',
                    'answer': 'Yes. Draw or upload your signature, place it on the PDF, and download the signed file.',
                },
            ],
        },
    )


def robots_txt_view(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /media/temp/',
        'Disallow: /media/signed/',
        'Disallow: /media/processed/',
        'Sitemap: /sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
