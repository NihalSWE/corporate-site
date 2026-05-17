from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from io import BytesIO
from PIL import Image

from .models import SisterConcern


class SisterConcernAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="password")
        self.client.force_login(self.user)

    def test_edit_updates_existing_sister_concern(self):
        concern = SisterConcern.objects.create(
            title="Old Concern",
            description="<p>Old description</p>",
            sort_order=1,
            is_active=True,
        )

        response = self.client.post(
            reverse("sister_concern_items"),
            {
                "action": "edit",
                "id": concern.id,
                "title": "Updated Concern",
                "description": "<p>Updated description</p>",
                "link": "https://example.com",
                "sort_order": "7",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("sister_concern_items"))
        concern.refresh_from_db()
        self.assertEqual(concern.title, "Updated Concern")
        self.assertEqual(concern.description, "<p>Updated description</p>")
        self.assertEqual(concern.link, "https://example.com")
        self.assertEqual(concern.sort_order, 7)
        self.assertTrue(concern.is_active)

    def test_edit_removes_display_image(self):
        image = BytesIO()
        Image.new("RGB", (360, 350), "white").save(image, format="JPEG")
        concern = SisterConcern.objects.create(
            title="Concern",
            description="<p>Description</p>",
            display_image=SimpleUploadedFile(
                "display.jpg",
                image.getvalue(),
                content_type="image/jpeg",
            ),
            sort_order=1,
            is_active=True,
        )

        response = self.client.post(
            reverse("sister_concern_items"),
            {
                "action": "edit",
                "id": concern.id,
                "title": "Concern",
                "description": "<p>Description</p>",
                "sort_order": "1",
                "is_active": "on",
                "remove_display_image": "1",
            },
        )

        self.assertRedirects(response, reverse("sister_concern_items"))
        concern.refresh_from_db()
        self.assertFalse(concern.display_image)
