from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from django.utils.text import slugify
import re

from .content_helpers import (
    delete_team_profile_description,
    get_contact_address_fields,
    attach_sister_concern_asset_urls,
    existing_file_url,
    load_team_profile_descriptions,
    pack_contact_addresses,
    SISTER_CONCERN_GALLERY_LIMIT,
    set_team_profile_description,
)
from .models import *
from .models import UserProfile

MAX_PROFILE_IMAGE_SIZE = 50 * 1024


def remove_uploaded_file(instance, field_name):
    file_field = getattr(instance, field_name, None)
    if file_field:
        file_field.delete(save=False)
        setattr(instance, field_name, "")


def clean_icon_class(value):
    value = (value or "").strip()
    match = re.search(r'class=["\']([^"\']+)["\']', value)
    if match:
        value = match.group(1)
    return re.sub(r"\s+", " ", value).strip()




def login_home(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard_home")

    return render(request, "login.html", {"form": form})


def signup_home(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username already exists.")
        else:
            new_user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.get_or_create(user=new_user)
            messages.success(request, "Account created. Please sign in.")
            return redirect("login_home")

    return render(request, "sign-up.html")


@login_required(login_url="login_home")
def dashboard_home(request):
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "breadcrumb": {"title": "Dashboard"},
            "layout": "light",
        },
    )


@login_required(login_url="login_home")
def users_home(request):
    users = User.objects.select_related("profile").order_by("-is_superuser", "-is_staff", "username")
    return render(
        request,
        "users/users.html",
        {
            "breadcrumb": {"title": "Users"},
            "layout": "light",
            "users": users,
        },
    )


@login_required(login_url="login_home")
def branding_admin(request):
    logo = Logo.objects.filter(is_active=True).first() or Logo.objects.first()
    favicon = WebsiteFavicon.objects.filter(is_active=True).first() or WebsiteFavicon.objects.first()
    header_setting = SiteHeaderSetting.objects.filter(is_active=True).first() or SiteHeaderSetting.objects.first()

    if request.method == "POST":
        logo_file = request.FILES.get("logo")
        favicon_file = request.FILES.get("favicon")
        top_message = request.POST.get("top_message", "").strip() or "Welcome to our consulting company."
        quote_button_text = request.POST.get("quote_button_text", "").strip() or "Get a quote"
        footer_description = request.POST.get("footer_description", "").strip()

        if len(top_message) > 80:
            messages.error(request, "Top header message must be 80 characters or fewer.")
            return redirect("home_identity")
        if len(quote_button_text) > 20:
            messages.error(request, "Quote button text must be 20 characters or fewer.")
            return redirect("home_identity")
        if len(footer_description) > 150:
            messages.error(request, "Footer description must be 150 characters or fewer.")
            return redirect("home_identity")

        try:
            header_setting = header_setting or SiteHeaderSetting()
            header_setting.top_message = top_message
            header_setting.quote_button_text = quote_button_text
            header_setting.footer_description = footer_description
            header_setting.is_active = True
            header_setting.full_clean()
            header_setting.save()
            SiteHeaderSetting.objects.exclude(pk=header_setting.pk).update(is_active=False)

            if logo_file:
                logo = logo or Logo()
                logo.image = logo_file
                logo.is_active = True
                logo.full_clean()
                logo.save()
                Logo.objects.exclude(pk=logo.pk).update(is_active=False)

            if favicon_file:
                favicon = favicon or WebsiteFavicon()
                favicon.image = favicon_file
                favicon.is_active = True
                favicon.full_clean()
                favicon.save()
                WebsiteFavicon.objects.exclude(pk=favicon.pk).update(is_active=False)

            messages.success(request, "Website branding saved successfully.")
        except Exception as exc:
            messages.error(request, str(exc))

        return redirect("home_identity")

    return render(
        request,
        "home/identity.html",
        {
            "breadcrumb": {"title": "Website Branding"},
            "layout": "light",
            "logo": logo,
            "favicon": favicon,
            "header_setting": header_setting,
        },
    )


@login_required(login_url="login_home")
def home_banner_admin(request):
    if request.method == "POST":
        action = request.POST.get("action", "save")

        try:
            if action == "delete":
                get_object_or_404(HomeBanner, id=request.POST.get("id")).delete()
                messages.success(request, "Home banner deleted successfully.")
                return redirect("banner")

            banner_id = request.POST.get("id")
            banner = get_object_or_404(HomeBanner, id=banner_id) if banner_id else HomeBanner()
            banner.title = request.POST.get("title", "").strip()
            banner.subtitle = request.POST.get("subtitle", "").strip()
            banner.description = request.POST.get("description", "").strip()
            banner.title_color = request.POST.get("title_color", "").strip()
            banner.subtitle_color = request.POST.get("subtitle_color", "").strip()
            banner.description_color = request.POST.get("description_color", "").strip()
            banner.sort_order = int(request.POST.get("sort_order") or 0)
            banner.is_active = bool(request.POST.get("is_active"))

            if request.FILES.get("image"):
                banner.image = request.FILES["image"]

            if len(banner.subtitle) > 15:
                messages.error(request, "Subtitle must be 15 characters or fewer.")
            elif len(banner.title) > 25:
                messages.error(request, "Title must be 25 characters or fewer.")
            elif len(banner.description) > 100:
                messages.error(request, "Description must be 100 characters or fewer.")
            elif not banner.image:
                messages.error(request, "Please upload the home banner image.")
            else:
                banner.full_clean()
                banner.save()
                messages.success(request, "Home banner saved successfully.")
        except Exception as exc:
            messages.error(request, str(exc))

        return redirect("banner")

    return render(
        request,
        "home/banner.html",
        {
            "breadcrumb": {"title": "Home Banner"},
            "layout": "light",
            "banners": HomeBanner.objects.all(),
        },
    )


@login_required(login_url="login_home")
def home_about_media_admin(request):
    media = HomeAboutMedia.objects.first()

    if request.method == "POST":
        media = media or HomeAboutMedia()
        media.video_url = None
        media.is_active = bool(request.POST.get("is_active"))

        if request.FILES.get("big_image"):
            media.big_image = request.FILES["big_image"]
        if request.FILES.get("small_image"):
            media.small_image = request.FILES["small_image"]

        if not media.big_image or not media.small_image:
            messages.error(request, "Big image and small image are required.")
        else:
            try:
                media.full_clean()
                media.save()
                messages.success(request, "Home about media saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))

        return redirect("home_about_media")

    return render(
        request,
        "home/about_media.html",
        {
            "breadcrumb": {"title": "Home About Media"},
            "layout": "light",
            "media": media,
        },
    )


@login_required(login_url="login_home")
def home_services_section_admin(request):
    section = HomeServiceSection.objects.first()

    if request.method == "POST":
        section = section or HomeServiceSection()
        section.title = request.POST.get("title", "").strip() or "We Offer Different Services"
        section.description = request.POST.get("description", "").strip()
        section.is_active = bool(request.POST.get("is_active"))

        if not section.description:
            messages.error(request, "Please enter the services section description.")
        elif len(section.title) > 120:
            messages.error(request, "Title must be 120 characters or fewer.")
        elif len(section.description) > 180:
            messages.error(request, "Description must be 180 characters or fewer.")
        else:
            try:
                section.full_clean()
                section.save()
                messages.success(request, "Home services text saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))

        return redirect("home_services_section")

    return render(
        request,
        "home/services_section.html",
        {
            "breadcrumb": {"title": "Home Services Text"},
            "layout": "light",
            "section": section,
        },
    )


@login_required(login_url="login_home")
def home_business_admin(request):
    section = HomeBusinessSection.objects.first()

    if request.method == "POST":
        section = section or HomeBusinessSection()
        section.small_title = request.POST.get("small_title", "").strip() or "Our Business"
        section.title = request.POST.get("title", "").strip() or "Stand Out From The Rest"
        section.is_active = bool(request.POST.get("is_active"))

        if len(section.small_title) > 30:
            messages.error(request, "Small title must be 30 characters or fewer.")
        elif len(section.title) > 40:
            messages.error(request, "Title must be 40 characters or fewer.")
        else:
            try:
                section.full_clean()
                section.save()

                for index in range(1, 4):
                    title = request.POST.get(f"item_title_{index}", "").strip()
                    description = request.POST.get(f"item_description_{index}", "").strip()
                    value_lines = request.POST.get(f"item_value_lines_{index}", "").strip()
                    item_id = request.POST.get(f"item_id_{index}", "").strip()

                    if not title and not description:
                        if item_id:
                            HomeBusinessItem.objects.filter(id=item_id).delete()
                        continue

                    if len(title) > 25:
                        messages.error(request, f"Card {index} title must be 25 characters or fewer.")
                        return redirect("home_business")
                    if index == 2:
                        value_count = len([line for line in value_lines.splitlines() if line.strip()])
                        if value_count > 6:
                            messages.error(request, "Core Values can have at most 6 bullet lines.")
                            return redirect("home_business")
                        if len(description) > 120:
                            messages.error(request, "Core Values description must be 120 characters or fewer.")
                            return redirect("home_business")
                    elif len(description) > 500:
                        messages.error(request, f"Card {index} description must be 500 characters or fewer.")
                        return redirect("home_business")
                    else:
                        value_lines = ""

                    if len(value_lines) > 300:
                        messages.error(request, f"Card {index} value lines must be 300 characters or fewer.")
                        return redirect("home_business")
                    item = HomeBusinessItem.objects.filter(id=item_id).first() if item_id else HomeBusinessItem()
                    item.title = title
                    item.description = description
                    item.value_lines = value_lines
                    item.sort_order = index
                    item.is_active = True
                    if request.FILES.get(f"item_icon_{index}"):
                        item.icon = request.FILES[f"item_icon_{index}"]
                    item.full_clean()
                    item.save()

                HomeBusinessItem.objects.filter(sort_order__gt=3).delete()
                messages.success(request, "Home business section saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))

        return redirect("home_business")

    items = list(HomeBusinessItem.objects.order_by("sort_order", "id")[:3])
    while len(items) < 3:
        items.append(None)

    return render(
        request,
        "home/business.html",
        {
            "breadcrumb": {"title": "Home Business"},
            "layout": "light",
            "section": section,
            "items": items,
        },
    )


@login_required(login_url="login_home")
def home_why_choose_admin(request):
    section = HomeWhyChooseSection.objects.first()

    if request.method == "POST":
        section = section or HomeWhyChooseSection()
        section.small_title = request.POST.get("small_title", "").strip() or "CHOICES & OCCURS"
        section.title = request.POST.get("title", "").strip() or "Why People Choose us"
        section.description = request.POST.get("description", "").strip()
        section.is_active = bool(request.POST.get("is_active"))

        if not section.description:
            messages.error(request, "Please enter the Why Choose Us description.")
        elif len(section.title) > 20:
            messages.error(request, "Title must be 20 characters or fewer.")
        elif len(section.description) > 120:
            messages.error(request, "Description must be 120 characters or fewer.")
        else:
            try:
                section.full_clean()
                section.save()

                item_indexes = request.POST.getlist("item_index")
                if not item_indexes:
                    item_indexes = [str(index) for index in range(1, 5)]

                for position, index in enumerate(item_indexes, start=1):
                    title = request.POST.get(f"item_title_{index}", "").strip()
                    description = request.POST.get(f"item_description_{index}", "").strip()
                    description_text = strip_tags(description).replace("&nbsp;", " ").strip()
                    item_id = request.POST.get(f"item_id_{index}", "").strip()

                    if not title and not description_text:
                        if item_id:
                            HomeWhyChooseItem.objects.filter(id=item_id).delete()
                        continue

                    if len(title) > 20:
                        messages.error(request, f"Card {index} title must be 20 characters or fewer.")
                        return redirect("home_why_choose")
                    if len(description_text) > 350:
                        messages.error(request, f"Card {position} description must be 350 characters or fewer.")
                        return redirect("home_why_choose")

                    item = HomeWhyChooseItem.objects.filter(id=item_id).first() if item_id else HomeWhyChooseItem()
                    item.title = title
                    item.description = description if description_text else ""
                    item.sort_order = position
                    item.is_active = True
                    item.full_clean()
                    item.save()

                messages.success(request, "Why Choose Us section saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))

        return redirect("home_why_choose")

    items = list(HomeWhyChooseItem.objects.order_by("sort_order", "id"))
    while len(items) < 4:
        items.append(None)

    return render(
        request,
        "home/why_choose.html",
        {
            "breadcrumb": {"title": "Home Why Choose Us"},
            "layout": "light",
            "section": section,
            "items": items,
        },
    )


@login_required(login_url="login_home")
def home_faq_admin(request):
    section = HomeFAQSection.objects.first()

    if request.method == "POST":
        section = section or HomeFAQSection()
        section.is_active = bool(request.POST.get("is_active"))

        if request.FILES.get("image"):
            section.image = request.FILES["image"]

        if not section.image:
            messages.error(request, "Please upload the FAQ image.")
            return redirect("home_faq")

        try:
            section.full_clean()
            section.save()

            for index in range(1, 5):
                question = request.POST.get(f"question_{index}", "").strip()
                answer = request.POST.get(f"answer_{index}", "").strip()
                item_id = request.POST.get(f"item_id_{index}", "").strip()

                if not question and not answer:
                    if item_id:
                        HomeFAQItem.objects.filter(id=item_id).delete()
                    continue

                item = HomeFAQItem.objects.filter(id=item_id).first() if item_id else HomeFAQItem()
                item.question = question
                item.answer = answer
                item.sort_order = index
                item.is_active = True
                item.full_clean()
                item.save()

            HomeFAQItem.objects.filter(sort_order__gt=4).delete()
            messages.success(request, "Home FAQ section saved successfully.")
        except Exception as exc:
            messages.error(request, str(exc))

        return redirect("home_faq")

    items = list(HomeFAQItem.objects.order_by("sort_order", "id")[:4])
    while len(items) < 4:
        items.append(None)

    return render(
        request,
        "home/faq.html",
        {
            "breadcrumb": {"title": "Home FAQ"},
            "layout": "light",
            "section": section,
            "items": items,
        },
    )


@login_required(login_url="login_home")
def home_mailing_subscribers_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            get_object_or_404(MailingSubscriber, id=request.POST.get("id")).delete()
            messages.success(request, "Subscriber deleted successfully.")
            return redirect("home_mailing_subscribers")

    return render(
        request,
        "home/mailing_subscribers.html",
        {
            "breadcrumb": {"title": "Mailing Subscribers"},
            "layout": "light",
            "subscribers": MailingSubscriber.objects.all(),
        },
    )


def admin_json(status, message):
    return JsonResponse({"status": status, "message": message})


@login_required(login_url="login_home")
def contact_banner_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "add":
                image = request.FILES.get("banner_image")
                if not image:
                    return admin_json("error", "Please upload a banner image.")

                ContactBanner.objects.create(
                    title=request.POST.get("title", "").strip() or "Contact",
                    banner_image=image,
                    is_active=bool(request.POST.get("is_active")),
                )
                return admin_json("success", "Contact banner saved successfully.")

            if action == "edit":
                banner = get_object_or_404(ContactBanner, id=request.POST.get("id"))
                banner.title = request.POST.get("title", "").strip() or "Contact"
                banner.is_active = bool(request.POST.get("is_active"))
                if request.FILES.get("banner_image"):
                    banner.banner_image = request.FILES["banner_image"]
                banner.save()
                return admin_json("success", "Contact banner updated successfully.")

            if action == "delete":
                get_object_or_404(ContactBanner, id=request.POST.get("id")).delete()
                return admin_json("success", "Contact banner deleted successfully.")
        except Exception as exc:
            return admin_json("error", str(exc))

        return admin_json("error", "Invalid action.")

    return render(
        request,
        "contactus/banner.html",
        {
            "breadcrumb": {"title": "Contact Banner"},
            "layout": "light",
            "banners": ContactBanner.objects.all().order_by("-id"),
        },
    )


@login_required(login_url="login_home")
def contact_info_admin(request):
    section = ContactSection.objects.first()
    info = ContactInfo.objects.first()

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "section":
            section = section or ContactSection()
            section.small_title = request.POST.get("small_title", "").strip() or "Contact Info to"
            section.title = request.POST.get("title", "").strip() or "Reach Our Expert Team"
            section.description = request.POST.get("description", "").strip()
            section.is_active = bool(request.POST.get("is_active"))

            if not section.description:
                messages.error(request, "Please enter the section description.")
            elif len(section.description) > 112:
                messages.error(request, "Description must be 112 characters or fewer.")
            else:
                section.save()
                messages.success(request, "Contact section saved successfully.")

        elif form_type == "info":
            info = info or ContactInfo()
            info.address_title = request.POST.get("address_title", "").strip() or "Post Address"
            info.address = pack_contact_addresses([
                request.POST.get("address_1", "").strip(),
                request.POST.get("address_2", "").strip(),
                request.POST.get("address_3", "").strip(),
            ])
            info.enquiry_title = request.POST.get("enquiry_title", "").strip() or "General Enquires"
            info.phone = request.POST.get("phone", "").strip()
            info.email = request.POST.get("email", "").strip()
            info.hours_title = request.POST.get("hours_title", "").strip() or "Operation Hours"
            info.operation_hours = request.POST.get("operation_hours", "").strip()
            info.facebook = request.POST.get("facebook", "").strip() or None
            info.youtube = request.POST.get("youtube", "").strip() or None
            info.whatsapp = request.POST.get("whatsapp", "").strip() or None
            info.is_active = bool(request.POST.get("is_active"))

            if not info.address or not info.phone or not info.email or not info.operation_hours:
                messages.error(request, "Address, phone, email, and operation hours are required.")
            else:
                info.save()
                messages.success(request, "Contact information saved successfully.")

        return redirect("contact_info_cards")

    return render(
        request,
        "contactus/info_cards.html",
        {
            "breadcrumb": {"title": "Contact Information"},
            "layout": "light",
            "section": section,
            "info": info,
            "address_fields": get_contact_address_fields(info.address if info else ""),
        },
    )


@login_required(login_url="login_home")
def contact_messages_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")
        message = get_object_or_404(ContactMessage, id=request.POST.get("id"))

        if action == "mark_read":
            message.is_read = True
            message.save(update_fields=["is_read"])
            return admin_json("success", "Message marked as read.")

        if action == "delete":
            message.delete()
            return admin_json("success", "Message deleted successfully.")

        return admin_json("error", "Invalid action.")

    return render(
        request,
        "contactus/messages.html",
        {
            "breadcrumb": {"title": "Contact Messages"},
            "layout": "light",
            "messages_list": ContactMessage.objects.all().order_by("-created_at"),
        },
    )


@login_required(login_url="login_home")
def contact_map_admin(request):
    map_obj = ContactMap.objects.first()

    if request.method == "POST":
        map_obj = map_obj or ContactMap()
        map_obj.map_title = request.POST.get("map_title", "").strip() or "Our Location"
        map_obj.map_embed_code = request.POST.get("map_embed_code", "").strip()
        map_obj.is_active = bool(request.POST.get("is_active"))

        if not map_obj.map_embed_code:
            messages.error(request, "Please paste the Google Maps embed iframe code.")
        else:
            map_obj.save()
            messages.success(request, "Contact map saved successfully.")

        return redirect("contact_map")

    return render(
        request,
        "contactus/map.html",
        {
            "breadcrumb": {"title": "Contact Map"},
            "layout": "light",
            "map_obj": map_obj,
        },
    )


@login_required(login_url="login_home")
def team_members_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "add":
                image = request.FILES.get("image")
                if not image:
                    return admin_json("error", "Please upload a team member image.")

                member = TeamMember.objects.create(
                    name=request.POST.get("name", "").strip(),
                    designation=request.POST.get("designation", "").strip(),
                    image=image,
                    facebook=request.POST.get("facebook", "").strip() or None,
                    linkedin=request.POST.get("linkedin", "").strip() or None,
                    twitter=request.POST.get("twitter", "").strip() or None,
                    youtube=request.POST.get("youtube", "").strip() or None,
                    sort_order=request.POST.get("sort_order") or 0,
                    is_active=bool(request.POST.get("is_active")),
                )
                set_team_profile_description(member.id, request.POST.get("description", ""))
                return admin_json("success", "Team member saved successfully.")

            if action == "edit":
                member = get_object_or_404(TeamMember, id=request.POST.get("id"))
                member.name = request.POST.get("name", "").strip()
                member.designation = request.POST.get("designation", "").strip()
                member.facebook = request.POST.get("facebook", "").strip() or None
                member.linkedin = request.POST.get("linkedin", "").strip() or None
                member.twitter = request.POST.get("twitter", "").strip() or None
                member.youtube = request.POST.get("youtube", "").strip() or None
                member.sort_order = request.POST.get("sort_order") or 0
                member.is_active = bool(request.POST.get("is_active"))
                if request.FILES.get("image"):
                    member.image = request.FILES["image"]
                member.save()
                set_team_profile_description(member.id, request.POST.get("description", ""))
                return admin_json("success", "Team member updated successfully.")

            if action == "delete":
                member_id = request.POST.get("id")
                get_object_or_404(TeamMember, id=member_id).delete()
                delete_team_profile_description(member_id)
                return admin_json("success", "Team member deleted successfully.")
        except Exception as exc:
            return admin_json("error", str(exc))

        return admin_json("error", "Invalid action.")

    members = list(TeamMember.objects.all())
    profile_descriptions = load_team_profile_descriptions()
    for member in members:
        member.profile_description = profile_descriptions.get(str(member.id), "")

    return render(
        request,
        "team/members.html",
        {
            "breadcrumb": {"title": "Our Team"},
            "layout": "light",
            "members": members,
        },
    )


@login_required(login_url="login_home")
def team_banner_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "add":
                image = request.FILES.get("banner_image")
                if not image:
                    return admin_json("error", "Please upload a banner image.")

                TeamBanner.objects.create(
                    title=request.POST.get("title", "").strip() or "Our Team",
                    banner_image=image,
                    is_active=bool(request.POST.get("is_active")),
                )
                return admin_json("success", "Our Team banner saved successfully.")

            if action == "edit":
                banner = get_object_or_404(TeamBanner, id=request.POST.get("id"))
                banner.title = request.POST.get("title", "").strip() or "Our Team"
                banner.is_active = bool(request.POST.get("is_active"))
                if request.FILES.get("banner_image"):
                    banner.banner_image = request.FILES["banner_image"]
                banner.save()
                return admin_json("success", "Our Team banner updated successfully.")

            if action == "delete":
                get_object_or_404(TeamBanner, id=request.POST.get("id")).delete()
                return admin_json("success", "Our Team banner deleted successfully.")
        except Exception as exc:
            return admin_json("error", str(exc))

        return admin_json("error", "Invalid action.")

    return render(
        request,
        "team/banner.html",
        {
            "breadcrumb": {"title": "Our Team Banner"},
            "layout": "light",
            "banners": TeamBanner.objects.all().order_by("-id"),
        },
    )


@login_required(login_url="login_home")
def sister_concern_banner_admin(request):
    banner = SisterConcernBanner.objects.first()

    if request.method == "POST":
        banner = banner or SisterConcernBanner()
        banner.title = request.POST.get("title", "").strip() or "Sister Concern"
        banner.is_active = bool(request.POST.get("is_active"))
        if request.FILES.get("banner_image"):
            banner.banner_image = request.FILES["banner_image"]

        if not banner.banner_image:
            messages.error(request, "Please upload a banner image.")
        else:
            try:
                banner.full_clean()
                banner.save()
                messages.success(request, "Sister Concern banner saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("sister_concern_banner")

    return render(
        request,
        "sister_concern/banner.html",
        {
            "breadcrumb": {"title": "Sister Concern Banner"},
            "layout": "light",
            "banner": banner,
        },
    )


@login_required(login_url="login_home")
def video_gallery_banner_admin(request):
    banner = VideoGalleryBanner.objects.first()

    if request.method == "POST":
        banner = banner or VideoGalleryBanner()
        banner.title = request.POST.get("title", "").strip() or "Video Gallery"
        banner.is_active = bool(request.POST.get("is_active"))
        if request.FILES.get("banner_image"):
            banner.banner_image = request.FILES["banner_image"]

        if not banner.banner_image:
            messages.error(request, "Please upload a banner image.")
        else:
            try:
                banner.full_clean()
                banner.save()
                messages.success(request, "Video Gallery banner saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("video_gallery_banner")

    return render(
        request,
        "gallery/video_banner.html",
        {
            "breadcrumb": {"title": "Video Gallery Banner"},
            "layout": "light",
            "banner": banner,
        },
    )


@login_required(login_url="login_home")
def photo_gallery_banner_admin(request):
    banner = PhotoGalleryBanner.objects.first()

    if request.method == "POST":
        banner = banner or PhotoGalleryBanner()
        banner.title = request.POST.get("title", "").strip() or "Photo Gallery"
        banner.is_active = bool(request.POST.get("is_active"))
        if request.FILES.get("banner_image"):
            banner.banner_image = request.FILES["banner_image"]

        if not banner.banner_image:
            messages.error(request, "Please upload a banner image.")
        else:
            try:
                banner.full_clean()
                banner.save()
                messages.success(request, "Photo Gallery banner saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("photo_gallery_banner")

    return render(
        request,
        "gallery/photo_banner.html",
        {
            "breadcrumb": {"title": "Photo Gallery Banner"},
            "layout": "light",
            "banner": banner,
        },
    )


@login_required(login_url="login_home")
def video_gallery_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                video_link = request.POST.get("url", "").strip() or None
                if not video_link:
                    messages.error(request, "Please enter a video link.")
                    return redirect("video_gallery_items")

                Video.objects.create(
                    title=request.POST.get("title", "").strip(),
                    url=video_link,
                    sort_order=request.POST.get("sort_order") or 0,
                    is_active=bool(request.POST.get("is_active")),
                )
                messages.success(request, "Video saved successfully.")

            elif action == "edit":
                video = get_object_or_404(Video, id=request.POST.get("id"))
                video.title = request.POST.get("title", "").strip()
                video.url = request.POST.get("url", "").strip() or None
                video.sort_order = request.POST.get("sort_order") or 0
                video.is_active = bool(request.POST.get("is_active"))
                if not video.url:
                    messages.error(request, "Please enter a video link.")
                else:
                    video.save()
                    messages.success(request, "Video updated successfully.")

            elif action == "delete":
                get_object_or_404(Video, id=request.POST.get("id")).delete()
                messages.success(request, "Video deleted successfully.")

            else:
                messages.error(request, "Invalid action.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("video_gallery_items")

    return render(
        request,
        "gallery/video_items.html",
        {
            "breadcrumb": {"title": "Video Gallery"},
            "layout": "light",
            "videos": Video.objects.all(),
        },
    )


@login_required(login_url="login_home")
def photo_gallery_admin(request):
    albums = Gallery_Album.objects.prefetch_related("images").all()

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add_album":
                thumbnail = request.FILES.get("thumbnail")
                if not thumbnail:
                    messages.error(request, "Please upload a thumbnail image.")
                    return redirect("photo_gallery_items")

                Gallery_Album.objects.create(
                    title=request.POST.get("title", "").strip(),
                    thumbnail=thumbnail,
                    sort_order=request.POST.get("sort_order") or 0,
                    is_active=bool(request.POST.get("is_active")),
                )
                messages.success(request, "Photo album saved successfully.")

            elif action == "edit_album":
                album = get_object_or_404(Gallery_Album, id=request.POST.get("id"))
                new_title = request.POST.get("title", "").strip()
                if album.title != new_title:
                    album.slug = ""
                album.title = new_title
                album.sort_order = request.POST.get("sort_order") or 0
                album.is_active = bool(request.POST.get("is_active"))
                if request.FILES.get("thumbnail"):
                    album.thumbnail = request.FILES["thumbnail"]
                album.save()
                messages.success(request, "Photo album updated successfully.")

            elif action == "delete_album":
                get_object_or_404(Gallery_Album, id=request.POST.get("id")).delete()
                messages.success(request, "Photo album deleted successfully.")

            elif action == "add_images":
                album = get_object_or_404(Gallery_Album, id=request.POST.get("album_id"))
                images = request.FILES.getlist("images")
                if not images:
                    messages.error(request, "Please upload at least one image.")
                    return redirect("photo_gallery_items")
                for image in images:
                    Gallery_AlbumDetails.objects.create(album=album, image=image)
                messages.success(request, f"{len(images)} image(s) saved successfully.")

            elif action == "delete_image":
                get_object_or_404(Gallery_AlbumDetails, id=request.POST.get("id")).delete()
                messages.success(request, "Image deleted successfully.")

            else:
                messages.error(request, "Invalid action.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("photo_gallery_items")

    return render(
        request,
        "gallery/photo_items.html",
        {
            "breadcrumb": {"title": "Photo Gallery"},
            "layout": "light",
            "albums": albums,
        },
    )


@login_required(login_url="login_home")
def about_banner_admin(request):
    banner = AboutPageBanner.objects.first()

    if request.method == "POST":
        banner = banner or AboutPageBanner()
        banner.title = request.POST.get("title", "").strip() or "About Us"
        banner.is_active = bool(request.POST.get("is_active"))
        if request.FILES.get("banner_image"):
            banner.banner_image = request.FILES["banner_image"]

        if not banner.banner_image:
            messages.error(request, "Please upload a banner image.")
        else:
            try:
                banner.full_clean()
                banner.save()
                messages.success(request, "About page banner saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("about_banner")

    return render(
        request,
        "about/banner.html",
        {
            "breadcrumb": {"title": "About Banner"},
            "layout": "light",
            "banner": banner,
        },
    )


@login_required(login_url="login_home")
def about_hero_admin(request):
    section = AboutHeroSection.objects.first()

    if request.method == "POST":
        section = section or AboutHeroSection()
        section.small_title = request.POST.get("small_title", "").strip() or "We are"
        section.title = request.POST.get("title", "").strip() or "Leaders in HR Solution"
        section.badge_text = request.POST.get("badge_text", "").strip()
        section.description = request.POST.get("description", "").strip()
        section.video_url = request.POST.get("video_url", "").strip() or None
        section.is_active = bool(request.POST.get("is_active"))

        if request.POST.get("remove_main_image") and not request.FILES.get("main_image"):
            remove_uploaded_file(section, "main_image")
        if request.POST.get("remove_video_thumbnail") and not request.FILES.get("video_thumbnail"):
            remove_uploaded_file(section, "video_thumbnail")

        if request.FILES.get("main_image"):
            section.main_image = request.FILES["main_image"]
        if request.FILES.get("video_thumbnail"):
            section.video_thumbnail = request.FILES["video_thumbnail"]

        description_text = strip_tags(section.description).replace("&nbsp;", " ").strip()

        if not description_text:
            messages.error(request, "Description is required.")
        else:
            try:
                section.full_clean(exclude=["main_image", "video_thumbnail"])
                if request.FILES.get("main_image"):
                    validate_about_hero_image(section.main_image)
                if request.FILES.get("video_thumbnail"):
                    validate_about_hero_image(section.video_thumbnail)
                section.save()
                messages.success(request, "About leaders section saved successfully.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("about_hero")

    return render(
        request,
        "about/hero.html",
        {
            "breadcrumb": {"title": "About Leaders Section"},
            "layout": "light",
            "section": section,
        },
    )


@login_required(login_url="login_home")
def profile_home(request):
    user = request.user
    UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        if request.POST.get("form_type") == "create_user":
            name = request.POST.get("name", "").strip()
            phone_number = request.POST.get("phone_number", "").strip()
            email = request.POST.get("new_email", "").strip()
            password = request.POST.get("new_password", "")
            image = request.FILES.get("image")

            if not name or not email or not password:
                messages.error(request, "Name, email, and password are required.")
                return redirect("profile_home")
            if image and image.size > MAX_PROFILE_IMAGE_SIZE:
                messages.error(request, "Image must be 50KB or smaller.")
                return redirect("profile_home")

            username_base = slugify(email.split("@")[0] or name).replace("-", "_")
            username = username_base or "user"
            counter = 1
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"{username_base}_{counter}"

            name_parts = name.split(maxsplit=1)
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else "",
            )
            UserProfile.objects.create(
                user=new_user,
                phone_number=phone_number,
                image=image,
            )
            messages.success(request, f"New user {username} created successfully.")
            return redirect("profile_home")

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")

        if not username:
            messages.error(request, "Username is required.")
        elif User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        else:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            if password:
                user.set_password(password)
            user.save()
            if password:
                update_session_auth_hash(request, user)
            messages.success(request, "Profile updated successfully.")
            return redirect("profile_home")

    return render(
        request,
        "profile/profile.html",
        {
            "breadcrumb": {"title": "Profile"},
            "layout": "light",
        },
    )


def logout_home(request):
    logout(request)
    return redirect("login_home")

@login_required(login_url="login_home")
def sister_concern_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "add":
                logo = request.FILES.get("logo")
                display_image = request.FILES.get("display_image")
                gallery_images = request.FILES.getlist("gallery_images")
                if len(gallery_images) > SISTER_CONCERN_GALLERY_LIMIT:
                    messages.error(request, "You can upload at most 10 gallery images.")
                    return redirect("sister_concern_items")
                for gallery_image in gallery_images:
                    validate_sister_concern_display_image(gallery_image)
                    gallery_image.seek(0)

                concern = SisterConcern(
                    title=request.POST.get("title", "").strip(),
                    description=request.POST.get("description", "").strip(),
                    logo=logo,
                    display_image=display_image,
                    link=request.POST.get("link", "").strip() or None,
                    sort_order=request.POST.get("sort_order") or 0,
                    is_active=bool(request.POST.get("is_active")),
                )
                concern.full_clean()
                concern.save()
                for index, gallery_image in enumerate(gallery_images, start=1):
                    SisterConcernGalleryImage.objects.create(
                        sister_concern=concern,
                        image=gallery_image,
                        sort_order=index,
                    )
                messages.success(request, "Sister concern saved successfully.")

            elif action == "edit":
                concern = get_object_or_404(SisterConcern, id=request.POST.get("id"))
                SisterConcernGalleryImage.objects.filter(
                    sister_concern=concern,
                    id__in=request.POST.getlist("remove_gallery_images"),
                ).delete()
                existing_gallery_count = concern.gallery_images.count()
                gallery_images = request.FILES.getlist("gallery_images")
                if existing_gallery_count + len(gallery_images) > SISTER_CONCERN_GALLERY_LIMIT:
                    messages.error(request, "Sister concern gallery can have at most 10 images.")
                    return redirect("sister_concern_items")
                for gallery_image in gallery_images:
                    validate_sister_concern_display_image(gallery_image)
                    gallery_image.seek(0)

                concern.title = request.POST.get("title", "").strip()
                concern.description = request.POST.get("description", "").strip()
                concern.link = request.POST.get("link", "").strip() or None
                concern.sort_order = request.POST.get("sort_order") or 0
                concern.is_active = bool(request.POST.get("is_active"))
                remove_logo = bool(request.POST.get("remove_logo")) and not request.FILES.get("logo")
                remove_display_image = bool(request.POST.get("remove_display_image")) and not request.FILES.get("display_image")
                if remove_logo and concern.logo:
                    concern.logo.delete(save=False)
                    concern.logo = None
                if remove_display_image and concern.display_image:
                    concern.display_image.delete(save=False)
                    concern.display_image = None
                if request.FILES.get("logo"):
                    concern.logo = request.FILES["logo"]
                if request.FILES.get("display_image"):
                    concern.display_image = request.FILES["display_image"]
                concern.full_clean()
                concern.save()
                next_order = existing_gallery_count + 1
                for offset, gallery_image in enumerate(gallery_images):
                    SisterConcernGalleryImage.objects.create(
                        sister_concern=concern,
                        image=gallery_image,
                        sort_order=next_order + offset,
                    )
                messages.success(request, "Sister concern updated successfully.")

            elif action == "delete":
                concern_id = request.POST.get("id")
                get_object_or_404(SisterConcern, id=concern_id).delete()
                messages.success(request, "Sister concern deleted successfully.")

            else:
                messages.error(request, "Invalid action.")
        except Exception as exc:
            messages.error(request, str(exc))

        return redirect("sister_concern_items")

    sister_concerns = list(SisterConcern.objects.all().order_by("sort_order", "title"))
    for concern in sister_concerns:
        attach_sister_concern_asset_urls(concern)
        concern.gallery_items = []
        for gallery_image in concern.gallery_images.all():
            gallery_image.existing_url = existing_file_url(gallery_image.image)
            if gallery_image.existing_url:
                concern.gallery_items.append(gallery_image)
        concern.gallery_slots_remaining = SISTER_CONCERN_GALLERY_LIMIT - len(concern.gallery_items)

    return render(
        request,
        "sister_concern/list.html",
        {
            "breadcrumb": {"title": "Sister Concern"},
            "layout": "light",
            "sister_concerns": sister_concerns,
        },
    )
