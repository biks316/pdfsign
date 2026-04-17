# PDFSign Studio (Django Monolith)

Production-minded, SEO-friendly document and image tools platform built with Django templates, vanilla JS, pdf.js, PyMuPDF, and Pillow.

## Included Apps

- `core`: homepage, robots.txt, global context, sitemap helpers
- `accounts`: profile page and account area
- `pdf_tools`: Sign PDF + Add Date to PDF
- `image_tools`: image conversion and optimization tools
- `pages`: About, FAQ, Privacy, Terms, Contact, How It Works

## Features Implemented

### PDF tools
- Sign PDF (draw signature and/or upload signature image)
- Place multiple signature/date overlays in preview
- Add Date to PDF (click placement with optional custom text)
- Preserves source content and overlays only stamped elements

### Image tools
- Image to PDF
- Resize image
- Compress image
- Crop image
- Convert PNG/JPG/WEBP
- Enhance scanned document image
- Remove background placeholder page + provider service abstraction

### SEO
- Clean URLs (`/pdf-tools/...`, `/image-tools/...`, `/pages/...`)
- Page-level title/meta description
- Open Graph tags and canonical tags
- FAQ schema on key pages
- Website schema in base template
- `sitemap.xml`
- `robots.txt` with media temp/processed exclusions
- Internal linking between related tools

### Authentication
- Email/password auth (django-allauth)
- Google OAuth wiring (allauth Google provider)
- Logout, password reset templates, account profile
- Auth architecture ready to add Microsoft provider later

## Quick Start

1. Create and activate virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables (see below).
4. Run migrations:

```bash
python manage.py migrate
```

5. Start dev server:

```bash
python manage.py runserver
```

6. Open `http://127.0.0.1:8000/`

## Environment Variables

```bash
DJANGO_SECRET_KEY=change-this
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_SITE_ID=1
SITE_NAME=PDFSign Studio
SITE_DOMAIN=http://127.0.0.1:8000
TIME_ZONE=America/New_York

# allauth behavior
ACCOUNT_EMAIL_VERIFICATION=optional

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_SECRET=
```

## Google OAuth Setup (django-allauth)

1. Create OAuth credentials in Google Cloud Console.
2. Add authorized redirect URI:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
3. In Django admin, create/update `Site` (`id=1`) with your domain.
4. In Django admin -> Social Applications:
   - Provider: Google
   - Client ID / Secret from Google
   - Attach site
5. Use Login/Signup pages and click `Continue with Google`.

## Production Notes

- Set `DJANGO_DEBUG=false`
- Configure `DJANGO_ALLOWED_HOSTS` and `SITE_DOMAIN`
- Use persistent storage for media (`temp`, `signed`, `processed`)
- Add scheduled cleanup for temporary/processed files
- Move static/media to CDN/object storage for scale
- Use Postgres instead of SQLite
- Add Celery/RQ for heavier file tasks

## URL Structure

- `/` Home
- `/pdf-tools/`
- `/pdf-tools/sign-pdf/`
- `/pdf-tools/add-date-to-pdf/`
- `/image-tools/`
- `/image-tools/image-to-pdf/`
- `/image-tools/resize-image/`
- `/image-tools/compress-image/`
- `/image-tools/crop-image/`
- `/image-tools/convert-image/`
- `/image-tools/remove-background/`
- `/image-tools/enhance-document/`
- `/pages/about/`
- `/pages/faq/`
- `/pages/privacy/`
- `/pages/terms/`
- `/pages/contact/`
- `/pages/how-it-works/`
- `/account/profile/`
- `/accounts/login/`, `/accounts/signup/`, OAuth routes

## Next Feature Suggestions

1. Merge PDF
2. Split PDF
3. Compress PDF
4. Reorder PDF pages
5. Saved signatures per user
6. Workflow/send-to-sign features
7. Background job queue for heavy tasks
8. S3-compatible object storage
9. Product analytics and event tracking
10. Ad placement zones for monetization
