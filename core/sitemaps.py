from django.urls import reverse
from django.contrib.sitemaps import Sitemap


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return [
            'core:home',
            'pdf_tools:index',
            'pdf_tools:sign_pdf',
            'pdf_tools:add_date',
            'image_tools:index',
            'image_tools:image_to_pdf',
            'image_tools:resize_image',
            'image_tools:compress_image',
            'image_tools:crop_image',
            'image_tools:convert_image',
            'image_tools:remove_background',
            'image_tools:enhance_document',
            'pages:about',
            'pages:faq',
            'pages:privacy',
            'pages:terms',
            'pages:contact',
            'pages:how_it_works',
        ]

    def location(self, item):
        return reverse(item)
