import re

from django.utils import timezone
from django.utils.safestring import mark_safe

from backend.models import (
    AboutHeroSection,
    ContactInfo,
    Gallery_AlbumDetails,
    Logo,
    SiteHeaderSetting,
    SisterConcern,
    WebsiteFavicon,
)
from backend.content_helpers import attach_sister_concern_asset_urls, split_contact_addresses


def sister_concerns(request):
    site_contact = ContactInfo.objects.filter(is_active=True).first() or ContactInfo.objects.first()
    site_whatsapp_url = ""
    current_year = timezone.localdate().year

    if site_contact and site_contact.whatsapp:
        whatsapp = site_contact.whatsapp.strip()
        if whatsapp.startswith(("http://", "https://")):
            site_whatsapp_url = whatsapp
        else:
            whatsapp_number = re.sub(r"\D", "", whatsapp)
            if whatsapp_number:
                site_whatsapp_url = f"https://wa.me/{whatsapp_number}"

    site_contact_addresses = split_contact_addresses(site_contact.address if site_contact else "")

    nav_sister_concerns = list(SisterConcern.objects.filter(is_active=True).order_by("sort_order", "title"))
    for concern in nav_sister_concerns:
        attach_sister_concern_asset_urls(concern)

    return {
        "nav_sister_concerns": nav_sister_concerns,
        "site_contact": site_contact,
        "site_contact_address": site_contact_addresses[0] if site_contact_addresses else "",
        "site_contact_addresses": site_contact_addresses,
        "site_whatsapp_url": site_whatsapp_url,
        "site_logo": Logo.objects.filter(is_active=True).first(),
        "site_favicon": WebsiteFavicon.objects.filter(is_active=True).first(),
        "site_header_setting": SiteHeaderSetting.objects.filter(is_active=True).first() or SiteHeaderSetting.objects.first(),
        "site_about": AboutHeroSection.objects.filter(is_active=True).first(),
        "modal_gallery_images": Gallery_AlbumDetails.objects.filter(is_active=True, album__is_active=True).order_by("?")[:5],
        "site_copyright": mark_safe(
            f'&copy; Copyright <a href="https://iglgroup.org/" target="_blank" rel="noopener">IGL Group</a> 2007-{current_year}<br>'
            'Domain Registered By <a href="https://iglweb.com/web/home.php" target="_blank" rel="noopener">IGL Web Ltd</a> | '
            'Hosting Service Provided by <a href="https://iglweb.com/web/home.php" target="_blank" rel="noopener">IGL Host Llc.com</a> | '
            'Web Design &amp; Development by <a href="https://iglweb.com/web/home.php" target="_blank" rel="noopener">IGL Web Ltd</a>'
        ),
    }
