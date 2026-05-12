from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from backend.models import *
from backend.forms import ContactMessageForm
from backend.content_helpers import (
    attach_sister_concern_asset_urls,
    get_team_profile_description,
    existing_file_url,
    split_contact_addresses,
)
from django.http import Http404
from urllib.parse import parse_qs, quote, urlparse
import re
# Create your views here.


def normalize_video_url(video_url, origin=""):
    if not video_url:
        return "", False

    parsed = urlparse(video_url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.strip("/")

    if host == "youtu.be":
        video_id = path.split("/")[0]
        return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&playsinline=1", False

    if host in {"youtube.com", "m.youtube.com"}:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if not video_id and path.startswith("embed/"):
            video_id = path.split("/", 1)[1]
        if not video_id and path.startswith("shorts/"):
            video_id = path.split("/", 1)[1]
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&playsinline=1", False

    if host == "vimeo.com" and path:
        video_id = path.split("/")[0]
        return f"https://player.vimeo.com/video/{video_id}?title=0&byline=0&portrait=0", False

    if host in {"facebook.com", "web.facebook.com", "m.facebook.com", "mobile.facebook.com", "fb.watch"}:
        encoded_url = quote(video_url, safe="")
        return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&show_text=false&width=900", False

    if video_url.lower().split("?")[0].endswith((".mp4", ".webm", ".ogg", ".mov", ".m4v")):
        return video_url, True

    return video_url, False


def build_map_embed_html(map_value):
    if not map_value:
        return ""

    map_value = map_value.strip()
    src_match = re.search(r'src=["\']([^"\']+)["\']', map_value, re.IGNORECASE)
    src = src_match.group(1) if src_match else map_value

    if not src.startswith(("http://", "https://")):
        return map_value if "<iframe" in map_value.lower() else ""

    return mark_safe(
        f'<iframe src="{escape(src)}" width="100%" height="450" style="border:0;" '
        'allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
    )

def home(request):
    if request.method == "POST" and request.POST.get("form_type") == "mailing_subscription":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please enter your email address.")
        elif MailingSubscriber.objects.filter(email__iexact=email).exists():
            messages.info(request, "This email is already subscribed.")
        else:
            try:
                MailingSubscriber.objects.create(email=email)
                messages.success(request, "Thank you for subscribing.")
            except Exception:
                messages.error(request, "Please enter a valid email address.")
        return redirect("home")

    about_section = AboutHeroSection.objects.filter(is_active=True).first()
    about_description = strip_tags(about_section.description).replace("&nbsp;", " ").strip() if about_section else ""
    about_excerpt = about_description[:500] + "..." if len(about_description) > 500 else about_description

    about_media = HomeAboutMedia.objects.filter(is_active=True).first()
    about_video_url = ""
    about_video_is_direct = False
    about_video_original_url = ""
    if about_media:
        about_video_original_url = about_media.video_url or ""
        about_video_url, about_video_is_direct = normalize_video_url(about_media.video_url)

    home_sister_concerns = list(SisterConcern.objects.filter(is_active=True))
    for concern in home_sister_concerns:
        attach_sister_concern_asset_urls(concern)

    return render(
        request,
        "index.html",
        {
            "logo": Logo.objects.filter(is_active=True).first(),
            "home_banners": HomeBanner.objects.filter(is_active=True),
            "home_about": about_section,
            "home_about_excerpt": about_excerpt,
            "home_about_media": about_media,
            "home_about_video_url": about_video_url,
            "home_about_video_is_direct": about_video_is_direct,
            "home_about_video_original_url": about_video_original_url,
            "home_business_section": HomeBusinessSection.objects.filter(is_active=True).first(),
            "home_business_items": HomeBusinessItem.objects.filter(is_active=True).order_by("sort_order", "id")[:3],
            "home_services_section": HomeServiceSection.objects.filter(is_active=True).first(),
            "home_sister_concerns": home_sister_concerns,
            "home_why_choose_section": HomeWhyChooseSection.objects.filter(is_active=True).first(),
            "home_why_choose_items": HomeWhyChooseItem.objects.filter(is_active=True).order_by("sort_order", "id")[:4],
            "home_faq_section": HomeFAQSection.objects.filter(is_active=True).first(),
            "home_faq_items": HomeFAQItem.objects.filter(is_active=True).order_by("sort_order", "id")[:4],
        },
    )


def aboutUs(request):
    hero_section = AboutHeroSection.objects.filter(is_active=True).first()
    video_url = ""
    video_is_direct = False
    video_original_url = ""
    if hero_section:
        origin = f"{request.scheme}://{request.get_host()}"
        video_original_url = hero_section.video_url or ""
        video_url, video_is_direct = normalize_video_url(hero_section.video_url, origin)
    has_about_media = bool(
        hero_section
        and (hero_section.main_image or hero_section.video_thumbnail)
    )

    return render(
        request,
        "aboutus/about-us.html",
        {
            "banner": AboutPageBanner.objects.filter(is_active=True).first(),
            "hero_section": hero_section,
            "video_url": video_url,
            "video_is_direct": video_is_direct,
            "video_original_url": video_original_url,
            "has_about_media": has_about_media,
        },
    )

def contact (request):
    form = ContactMessageForm()
    banner = ContactBanner.objects.filter(
            is_active=True
        ).first()

    section = ContactSection.objects.filter(
        is_active=True
    ).first()

    info = ContactInfo.objects.filter(
        is_active=True
    ).first()
    whatsapp_link = ""
    if info and info.whatsapp:
        whatsapp_number = re.sub(r"\D", "", info.whatsapp)
        if whatsapp_number:
            whatsapp_link = f"https://wa.me/{whatsapp_number}"

    map_data = ContactMap.objects.filter(
        is_active=True
    ).first()
    map_embed_html = build_map_embed_html(map_data.map_embed_code) if map_data else ""

    if request.method == "POST":
        form = ContactMessageForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your message has been sent successfully."
            )

            next_url = request.POST.get("next", "").strip()
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)

            return redirect("contact")

    else:
        form = ContactMessageForm()

    context = {
        "banner": banner,
        "section": section,
        "info": info,
        "contact_addresses": split_contact_addresses(info.address if info else ""),
        "map_data": map_data,
        "map_embed_html": map_embed_html,
        "form": form,
        "whatsapp_link": whatsapp_link,
    }
    return render(request, "contact/contact.html", context)

def ourteam(request):
    return render(
        request,
        "ourteam/our-team.html",
        {
            "banner": TeamBanner.objects.filter(is_active=True).first(),
            "team_members": TeamMember.objects.filter(is_active=True),
        },
    )


def team_member_slug(member):
    return slugify(member.name) or f"team-member-{member.id}"


def team_member_detail_by_id(request, member_id):
    member = get_object_or_404(TeamMember, id=member_id, is_active=True)
    return redirect("team_member_detail", member_slug=team_member_slug(member), permanent=True)


def team_member_detail(request, member_slug):
    member = None
    for team_member in TeamMember.objects.filter(is_active=True):
        if team_member_slug(team_member) == member_slug:
            member = team_member
            break
    if member is None:
        raise Http404("Team member not found")

    return render(
        request,
        "ourteam/team-detail.html",
        {
            "banner": TeamBanner.objects.filter(is_active=True).first(),
            "member": member,
            "profile_description": get_team_profile_description(member.id),
        },
    )


def sister_concern_detail(request, slug):
    concern = get_object_or_404(SisterConcern, slug=slug, is_active=True)
    attach_sister_concern_asset_urls(concern)
    return render(
        request,
        "sister_concern/detail.html",
        {
            "banner": SisterConcernBanner.objects.filter(is_active=True).first(),
            "concern": concern,
            "gallery_images": [
                existing_file_url(gallery_image.image)
                for gallery_image in concern.gallery_images.all()
                if existing_file_url(gallery_image.image)
            ],
        },
    )


def video_gallery(request):
    return render(
        request,
        "gallery/video-gallery.html",
        {
            "banner": VideoGalleryBanner.objects.filter(is_active=True).first(),
            "videos": Video.objects.filter(is_active=True),
        },
    )


def photo_gallery(request):
    return render(
        request,
        "gallery/photo-gallery.html",
        {
            "banner": PhotoGalleryBanner.objects.filter(is_active=True).first(),
            "albums": Gallery_Album.objects.filter(is_active=True),
        },
    )


def photo_gallery_detail(request, slug):
    album = get_object_or_404(Gallery_Album, slug=slug, is_active=True)
    return render(
        request,
        "gallery/photo-gallery-detail.html",
        {
            "banner": PhotoGalleryBanner.objects.filter(is_active=True).first(),
            "album": album,
            "images": album.images.filter(is_active=True),
        },
    )
