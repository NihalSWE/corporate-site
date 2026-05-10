from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(Logo)
admin.site.register(WebsiteFavicon)
admin.site.register(AboutPageBanner)
admin.site.register(AboutHeroSection)
admin.site.register(Gallery_Album)
admin.site.register(Gallery_AlbumDetails)
admin.site.register(Video)
admin.site.register(SisterConcern)
admin.site.register(SisterConcernBanner)
admin.site.register(VideoGalleryBanner)
admin.site.register(PhotoGalleryBanner)
admin.site.register(TeamMember)
admin.site.register(TeamBanner)

@admin.register(ContactBanner)
class ContactBannerAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active"]


@admin.register(ContactSection)
class ContactSectionAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active"]


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ["email", "phone", "is_active"]


@admin.register(ContactMap)
class ContactMapAdmin(admin.ModelAdmin):
    list_display = [
        "map_title",
        "is_active"
    ]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "subject",
        "created_at",
        "is_read"
    ]

    list_filter = [
        "is_read",
        "created_at"
    ]

    search_fields = [
        "name",
        "email",
        "subject",
        "message"
    ]
