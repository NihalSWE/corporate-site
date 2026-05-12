from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.text import slugify
from io import BytesIO
from PIL import Image
import re


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=30, blank=True)
    image = models.FileField(upload_to="user_profiles/", blank=True, null=True)

    def __str__(self):
        return self.user.username



# =========================
# Contact Banner Validation
# =========================
def validate_banner_image(image):
    max_size = 100 * 1024

    if image.size > max_size:
        raise ValidationError("Banner image size must not exceed 100KB.")

    img = Image.open(image)
    width, height = img.size

    if width != 1907 or height != 323:
        raise ValidationError("Banner image size must be exactly 1907x323 pixels.")


def validate_team_member_image(image):
    max_size = 25 * 1024

    if image.size > max_size:
        raise ValidationError("Team member image size must not exceed 25KB.")

    img = Image.open(image)
    width, height = img.size

    if width != 354 or height != 373:
        raise ValidationError("Team member image size must be exactly 354x373 pixels.")


def validate_about_hero_image(image):
    max_size = 25 * 1024

    if image.size > max_size:
        raise ValidationError("About section image size must not exceed 25KB.")

    img = Image.open(image)
    width, height = img.size

    if width != 273 or height != 372:
        raise ValidationError("About section image size must be exactly 273x372 pixels.")


def validate_about_badge_image(image):
    max_size = 5 * 1024

    if image.size > max_size:
        raise ValidationError("Badge image size must not exceed 5KB.")

    img = Image.open(image)
    width, height = img.size

    if width != 52 or height != 52:
        raise ValidationError("Badge image size must be exactly 52x52 pixels.")


def validate_about_business_image(image):
    img = Image.open(image)
    width, height = img.size

    if width != 353 or height != 265:
        raise ValidationError("Business section image size must be exactly 353x265 pixels.")


def validate_about_video_file(video):
    allowed_extensions = (".mp4", ".webm", ".ogg")
    if not video.name.lower().endswith(allowed_extensions):
        raise ValidationError("Video must be MP4, WEBM, or OGG.")


def validate_gallery_video_file(video):
    allowed_extensions = (".mp4", ".webm", ".ogg", ".mov", ".m4v", ".avi", ".mkv")
    if not video.name.lower().endswith(allowed_extensions):
        raise ValidationError("Video must be MP4, WEBM, OGG, MOV, M4V, AVI, or MKV.")


def validate_website_brand_image(image):
    max_size = 10 * 1024

    if image.size > max_size:
        raise ValidationError("Image size must not exceed 10KB.")


def validate_exact_image(image, width, height, max_size, label):
    if image.size > max_size:
        raise ValidationError(f"{label} image size must not exceed {max_size // 1024}KB.")

    img = Image.open(image)
    actual_width, actual_height = img.size

    if actual_width != width or actual_height != height:
        raise ValidationError(f"{label} image size must be exactly {width}x{height} pixels.")


def validate_max_image(image, width, height, max_size, label):
    if image.size > max_size:
        raise ValidationError(f"{label} image size must not exceed {max_size // 1024}KB.")

    img = Image.open(image)
    actual_width, actual_height = img.size

    if actual_width > width or actual_height > height:
        raise ValidationError(f"{label} image size must not be larger than {width}x{height} pixels.")


def validate_home_banner_image(image):
    validate_max_image(image, 1920, 850, 200 * 1024, "Home banner")


def validate_home_about_big_image(image):
    validate_exact_image(image, 540, 570, 50 * 1024, "Home about big")


def validate_home_about_small_image(image):
    validate_exact_image(image, 300, 200, 50 * 1024, "Home about small")


def validate_home_faq_image(image):
    validate_exact_image(image, 1000, 1000, 100 * 1024, "Home FAQ")


def validate_sister_concern_display_image(image):
    validate_exact_image(image, 360, 350, 50 * 1024, "Sister concern")


def optimize_image_file(path, size=None, max_size=100 * 1024):
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if size:
        img.thumbnail(size, Image.Resampling.LANCZOS)

    quality = 85
    while quality >= 35:
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= max_size or quality == 35:
            with open(path, "wb") as image_file:
                image_file.write(buffer.getvalue())
            break
        quality -= 8


# =========================
# Contact Banner
# =========================
class ContactBanner(models.Model):
    title = models.CharField(max_length=100, default="Contact")

    banner_image = models.ImageField(
        upload_to="contact/banner/",
        validators=[validate_banner_image]
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# =========================
# Contact Section Title
# =========================
class ContactSection(models.Model):
    small_title = models.CharField(
        max_length=100,
        default="Contact Info to"
    )

    title = models.CharField(
        max_length=150,
        default="Reach Our Expert Team"
    )

    description = models.TextField(max_length=112)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# =========================
# Contact Information
# =========================
class ContactInfo(models.Model):
    address_title = models.CharField(
        max_length=100,
        default="Post Address"
    )

    address = models.TextField()

    enquiry_title = models.CharField(
        max_length=100,
        default="General Enquires"
    )

    phone = models.CharField(max_length=50)

    email = models.EmailField()

    hours_title = models.CharField(
        max_length=100,
        default="Operation Hours"
    )

    operation_hours = models.CharField(max_length=150)

    facebook = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    whatsapp = models.CharField(max_length=30, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email


# =========================
# Contact Map
# =========================
class ContactMap(models.Model):
    map_title = models.CharField(
        max_length=150,
        default="Our Location"
    )

    map_embed_code = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.map_title


# =========================
# Contact Form Messages
# =========================
class ContactMessage(models.Model):
    name = models.CharField(max_length=150)

    email = models.EmailField()

    subject = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.email}"


class TeamMember(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=120)
    image = models.ImageField(
        upload_to="team/",
        validators=[validate_team_member_image],
    )
    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name


class TeamBanner(models.Model):
    title = models.CharField(max_length=100, default="Our Team")
    banner_image = models.ImageField(
        upload_to="team/banner/",
        validators=[validate_banner_image],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class SisterConcernBanner(models.Model):
    title = models.CharField(max_length=100, default="Sister Concern")
    banner_image = models.ImageField(
        upload_to="sister_concerns/banner/",
        validators=[validate_banner_image],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# =========================
# Website Logo
# =========================
class Logo(models.Model):
    image = models.ImageField(upload_to="logos/", validators=[validate_website_brand_image])
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            img.thumbnail((200, 200))
            img.save(self.image.path)

    def __str__(self):
        return "Logo"


class WebsiteFavicon(models.Model):
    image = models.ImageField(upload_to="favicons/", validators=[validate_website_brand_image])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Website Favicon"


class SiteHeaderSetting(models.Model):
    top_message = models.CharField(max_length=80, default="Welcome to our consulting company.")
    quote_button_text = models.CharField(max_length=20, default="Get a quote")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.top_message


# =========================
# Home Page
# =========================
class HomeBanner(models.Model):
    title = models.CharField(max_length=25)
    subtitle = models.CharField(max_length=15)
    description = models.CharField(max_length=100)
    title_color = models.CharField(max_length=7, blank=True, default="")
    subtitle_color = models.CharField(max_length=7, blank=True, default="")
    description_color = models.CharField(max_length=7, blank=True, default="")
    image = models.ImageField(upload_to="home/banner/", validators=[validate_home_banner_image])
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return self.title


class HomeAboutMedia(models.Model):
    big_image = models.ImageField(upload_to="home/about/", validators=[validate_home_about_big_image])
    small_image = models.ImageField(upload_to="home/about/", validators=[validate_home_about_small_image])
    video_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Home About Media"


class HomeServiceSection(models.Model):
    title = models.CharField(max_length=120, default="We Offer Different Services")
    description = models.CharField(
        max_length=180,
        default="There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form believable.",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class HomeBusinessSection(models.Model):
    small_title = models.CharField(max_length=30, default="Our Business")
    title = models.CharField(max_length=40, default="Stand Out From The Rest")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class HomeBusinessItem(models.Model):
    title = models.CharField(max_length=25)
    description = models.CharField(max_length=500, blank=True, default="")
    icon = models.ImageField(upload_to="home/business/", blank=True, null=True)
    value_lines = models.TextField(
        max_length=300,
        blank=True,
        default="",
        help_text="For the middle Core Values card only. Add one value per line, max 6 lines.",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title

    def values_list(self):
        return [line.strip() for line in self.value_lines.splitlines() if line.strip()]


class HomeWhyChooseSection(models.Model):
    small_title = models.CharField(max_length=80, default="CHOICES & OCCURS")
    title = models.CharField(max_length=20, default="Why People Choose us")
    description = models.CharField(
        max_length=120,
        default="Explain to you how all this mistaken idea of denouncing pleasure and praising pain was born and I will give you a complete account of the system.",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class HomeWhyChooseItem(models.Model):
    title = models.CharField(max_length=20)
    description = models.CharField(max_length=80)
    icon = models.ImageField(upload_to="home/why_choose/", blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class HomeFAQSection(models.Model):
    image = models.ImageField(upload_to="home/faq/", validators=[validate_home_faq_image])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Home FAQ Section"


class HomeFAQItem(models.Model):
    question = models.CharField(max_length=220)
    answer = models.TextField(max_length=700)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class MailingSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


# =========================
# About Page
# =========================
class AboutPageBanner(models.Model):
    title = models.CharField(max_length=100, default="About Us")
    banner_image = models.ImageField(
        upload_to="about/banner/",
        validators=[validate_banner_image],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class AboutHeroSection(models.Model):
    small_title = models.CharField(max_length=100, default="We are")
    title = models.CharField(max_length=180, default="Leaders in HR Solution")
    badge_text = models.CharField(max_length=150, default="Since 1998, Operating in Birmingham.")
    badge_image = models.ImageField(
        upload_to="about/hero/badge/",
        validators=[validate_about_badge_image],
        blank=True,
        null=True,
    )
    description = models.TextField()
    main_image = models.ImageField(
        upload_to="about/hero/",
        validators=[validate_about_hero_image],
    )
    video_thumbnail = models.ImageField(
        upload_to="about/hero/",
        validators=[validate_about_hero_image],
    )
    video_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# =========================
# Gallery Page
# =========================
class VideoGalleryBanner(models.Model):
    title = models.CharField(max_length=100, default="Video Gallery")
    banner_image = models.ImageField(
        upload_to="gallery/video/banner/",
        validators=[validate_banner_image],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PhotoGalleryBanner(models.Model):
    title = models.CharField(max_length=100, default="Photo Gallery")
    banner_image = models.ImageField(
        upload_to="gallery/photo/banner/",
        validators=[validate_banner_image],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Gallery_Album(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.ImageField(upload_to="albums/thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title if self.title else f"Gallery_Album {self.id}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title or "gallery-album")
            unique_slug = base_slug
            counter = 1
            while Gallery_Album.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
        if self.thumbnail:
            optimize_image_file(self.thumbnail.path, size=(560, 340))


class Gallery_AlbumDetails(models.Model):
    album = models.ForeignKey(Gallery_Album, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="gallery/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "-uploaded_at"]

    def __str__(self):
        return self.album.title if self.album and self.album.title else f"Image {self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            optimize_image_file(self.image.path, size=(900, 620))


class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(help_text="YouTube, Vimeo, Facebook, or direct video link", blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def frontend_video_url(self):
        if self.url:
            return self.embed_url()
        return ""

    def original_video_url(self):
        return self.url or ""

    def is_direct_video(self):
        video_url = self.frontend_video_url()
        return bool(video_url and video_url.lower().split("?")[0].endswith((".mp4", ".webm", ".ogg", ".mov", ".m4v")))

    def is_iframe_video(self):
        return bool(self.frontend_video_url() and not self.is_direct_video())

    def thumbnail_url(self):
        if not self.url:
            return ""
        youtube_pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]+)"
        youtube_match = re.search(youtube_pattern, self.url)
        if youtube_match:
            return f"https://img.youtube.com/vi/{youtube_match.group(1)}/hqdefault.jpg"
        return ""

    def embed_url(self):
        if not self.url:
            return ""
        youtube_pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]+)"
        vimeo_pattern = r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)"
        facebook_pattern = r"(?:https?:\/\/)?(?:(?:www|web|m|mobile)\.)?(?:facebook\.com|fb\.watch)\/.+"
        youtube_match = re.search(youtube_pattern, self.url)
        vimeo_match = re.search(vimeo_pattern, self.url)
        facebook_match = re.search(facebook_pattern, self.url)

        if youtube_match:
            return f"https://www.youtube.com/embed/{youtube_match.group(1)}?rel=0&modestbranding=1&playsinline=1"
        if vimeo_match:
            return f"https://player.vimeo.com/video/{vimeo_match.group(1)}?title=0&byline=0&portrait=0"
        if facebook_match:
            from urllib.parse import quote
            return f"https://www.facebook.com/plugins/video.php?href={quote(self.url, safe='')}&show_text=false&width=900"
        return self.url


class SisterConcern(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to="sister_concerns/logos/", blank=True, null=True)
    display_image = models.ImageField(
        upload_to="sister_concerns/images/",
        validators=[validate_sister_concern_display_image],
        blank=True,
        null=True,
    )
    link = models.URLField(max_length=200, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            counter = 1
            while SisterConcern.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        super().save(*args, **kwargs)

        if self.logo:
            try:
                logo = Image.open(self.logo.path)
            except (FileNotFoundError, ValueError):
                return
            logo.thumbnail((420, 160), Image.Resampling.LANCZOS)
            logo.save(self.logo.path)


class SisterConcernGalleryImage(models.Model):
    sister_concern = models.ForeignKey(
        SisterConcern,
        related_name="gallery_images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to="sister_concerns/gallery/",
        validators=[validate_sister_concern_display_image],
        blank=True,
        null=True,
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.sister_concern.title if self.sister_concern_id else f"Gallery image {self.id}"

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)
