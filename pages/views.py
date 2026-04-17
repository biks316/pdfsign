from django.shortcuts import render


def about_view(request):
    return render(request, 'pages/about.html', {
        'page_title': 'About PDFSign Studio',
        'meta_description': 'Learn about PDFSign Studio and our approach to simple, secure, and fast document tools.',
        'canonical_path': '/pages/about/',
    })


def faq_view(request):
    faq_items = [
        {
            'question': 'Is this platform free to use?',
            'answer': 'Core tools are available without paid plans in this version.',
        },
        {
            'question': 'How does Sign PDF work?',
            'answer': 'Upload a PDF, draw or upload your signature, click where it should appear, and download the output.',
        },
        {
            'question': 'Do you modify my original file?',
            'answer': 'No. A new output file is generated while preserving source content and overlaying only edits.',
        },
    ]
    return render(request, 'pages/faq.html', {
        'page_title': 'FAQ | PDFSign Studio',
        'meta_description': 'Common questions about signing PDFs, image tools, file privacy, and workflows.',
        'canonical_path': '/pages/faq/',
        'faq_items': faq_items,
        'faq_schema': faq_items,
    })


def privacy_view(request):
    return render(request, 'pages/privacy.html', {
        'page_title': 'Privacy Policy | PDFSign Studio',
        'meta_description': 'Privacy policy for PDFSign Studio covering file handling, storage, and account information.',
        'canonical_path': '/pages/privacy/',
    })


def terms_view(request):
    return render(request, 'pages/terms.html', {
        'page_title': 'Terms of Service | PDFSign Studio',
        'meta_description': 'Terms of service for using PDFSign Studio document and image tools.',
        'canonical_path': '/pages/terms/',
    })


def contact_view(request):
    return render(request, 'pages/contact.html', {
        'page_title': 'Contact | PDFSign Studio',
        'meta_description': 'Contact PDFSign Studio for support, partnership requests, and product feedback.',
        'canonical_path': '/pages/contact/',
    })


def how_it_works_view(request):
    return render(request, 'pages/how_it_works.html', {
        'page_title': 'How It Works | PDFSign Studio',
        'meta_description': 'See how to use PDF and image tools in simple steps, from upload to download.',
        'canonical_path': '/pages/how-it-works/',
    })
