# PDF Signer (Django + pdf.js + PyMuPDF)

A simple server-rendered Django web app to upload a PDF, draw a signature, click to place it on a page, optionally add the current date, and download a signed PDF.

## Features

- Upload PDF file
- Browser PDF preview using pdf.js
- Draw signature on an HTML canvas
- Click on pages multiple times to place one or more signatures
- Optional current date next to signature
- Preview placement in the browser
- Save and download signed PDF

## Tech Stack

- Django (server-rendered templates)
- Vanilla JavaScript
- pdf.js (CDN)
- PyMuPDF (`fitz`)

## Project Structure

- `pdfsign_project/` Django project settings and root URLs
- `signer/` App with forms, views, URLs, templates, static files
- `media/temp/` Uploaded PDFs
- `media/signed/` Signed PDFs

## Setup

1. Create and activate a virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations (safe even though this app does not require custom models):

```bash
python manage.py migrate
```

4. Start dev server:

```bash
python manage.py runserver
```

5. Open `http://127.0.0.1:8000/`

## Usage Flow

1. Upload a PDF.
2. Draw signature in the signature canvas.
3. Click anywhere on rendered PDF pages to add one or more placements.
4. Optionally check **Add current date next to each signature**.
5. Click **Save and Download Signed PDF**.

## Notes

- This is intentionally minimal and does not include auth.
- Signature placement uses relative coordinates from the browser preview.
- Basic validation and error handling are included for file type and signing inputs.
