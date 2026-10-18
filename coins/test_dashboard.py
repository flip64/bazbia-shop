from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from . import models as m


class CatalogDashboardTests(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects.create_superuser(
            "manager", "test@example.com", "test"
        )
        self.staff = get_user_model().objects.create_user(
            "staff", password="test", is_staff=True
        )
        self.issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        self.coin = m.CoinType.objects.create(
            name="سکه خصوصی", slug="private", issuer=self.issuer
        )
        self.client.force_login(self.manager)

    def url(self, name, **kwargs):
        return reverse("dashboard:coin_catalog:" + name, kwargs=kwargs)

    def payload(self):
        return {
            "name": "سکه ویرایش‌شده",
            "slug": "private",
            "issuer": self.issuer.pk,
            "calendar": "gregorian",
            "issue_kind": "circulation",
            "construction": "unknown",
            "shape": "round",
            "edge_type": "unknown",
            "story": "## داستان\n\nروایت تاریخی",
        }

    def test_guest_redirects_to_real_admin_login(self):
        self.client.logout()
        response = self.client.get(self.url("list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/?next="))

    def test_staff_without_model_permission_cannot_read_or_write(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url("list")).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.url("edit", kind="type", pk=self.coin.pk), self.payload()
            ).status_code,
            403,
        )
        self.coin.refresh_from_db()
        self.assertEqual(self.coin.name, "سکه خصوصی")

    def test_view_only_staff_can_read_but_cannot_change(self):
        self.staff.user_permissions.add(
            Permission.objects.get(codename="view_cointype")
        )
        self.client.force_login(self.staff)
        self.assertContains(
            self.client.get(self.url("detail", pk=self.coin.pk)), "سکه خصوصی"
        )
        self.assertEqual(
            self.client.get(self.url("edit", kind="type", pk=self.coin.pk)).status_code,
            403,
        )

    def test_internal_catalog_visible_without_any_sale(self):
        self.assertContains(self.client.get(self.url("list")), "سکه خصوصی")
        self.assertContains(
            self.client.get(self.url("detail", pk=self.coin.pk)),
            "ویرایش مشخصات و داستان",
        )
        self.assertEqual(self.client.get("/api/coins/").data["count"], 0)

    def test_update_story_and_fields(self):
        response = self.client.post(
            self.url("edit", kind="type", pk=self.coin.pk), self.payload()
        )
        self.assertEqual(
            response.status_code,
            302,
            response.context["form"].errors if response.status_code == 200 else "",
        )
        self.coin.refresh_from_db()
        self.assertEqual(self.coin.name, "سکه ویرایش‌شده")
        self.assertIn("روایت تاریخی", self.coin.story)

    def test_invalid_issue_is_not_saved(self):
        data = {
            "coin_type": self.coin.pk,
            "year": 2000,
            "calendar": "solar_hijri",
            "date_status": "known",
            "finish": "unknown",
        }
        response = self.client.post(self.url("create", kind="issue"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(m.CoinIssue.objects.exists())

    def test_create_issue_uses_coin_calendar_and_returns_to_coin(self):
        url = self.url("create", kind="issue") + "?coin=" + str(self.coin.pk)
        self.assertEqual(
            self.client.get(url).context["form"].initial["calendar"], "gregorian"
        )
        response = self.client.post(
            url,
            {
                "coin_type": self.coin.pk,
                "year": 2000,
                "calendar": "gregorian",
                "date_status": "known",
                "finish": "unknown",
                "description": "داستان سال",
            },
        )
        self.assertRedirects(response, self.url("detail", pk=self.coin.pk))
        issue = m.CoinIssue.objects.get()
        self.assertContains(
            self.client.get(self.url("record-detail", kind="issue", pk=issue.pk)),
            "داستان سال",
        )

    def test_create_reference_image_and_reject_wrong_issue(self):
        data = {
            "coin_type": self.coin.pk,
            "source_url": "https://example.com/reference.jpg",
            "view_type": "obverse",
            "position": 0,
            "caption": "تصویر مرجع",
        }
        response = self.client.post(self.url("create", kind="image"), data)
        self.assertEqual(response.status_code, 302)
        other = m.CoinType.objects.create(name="دیگر", slug="other", issuer=self.issuer)
        issue = m.CoinIssue.objects.create(coin_type=other, year=2000)
        data["issue"] = issue.pk
        response = self.client.post(self.url("create", kind="image"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(m.CoinCatalogImage.objects.count(), 1)

    def test_unknown_model_and_get_do_not_mutate(self):
        self.assertEqual(
            self.client.get(self.url("records", kind="users")).status_code, 404
        )
        self.client.get(self.url("edit", kind="type", pk=self.coin.pk))
        self.coin.refresh_from_db()
        self.assertEqual(self.coin.name, "سکه خصوصی")

    def test_csrf_required_for_writes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        response = client.post(
            self.url("edit", kind="type", pk=self.coin.pk), self.payload()
        )
        self.assertEqual(response.status_code, 403)

    def test_html_in_story_is_escaped_in_staff_detail(self):
        self.coin.story = "<script>alert(1)</script>"
        self.coin.save()
        response = self.client.get(self.url("detail", pk=self.coin.pk))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_all_registered_forms_render(self):
        from .dashboard_views import MODELS

        for kind in MODELS:
            with self.subTest(kind=kind):
                self.assertEqual(
                    self.client.get(self.url("create", kind=kind)).status_code, 200
                )
                self.assertEqual(
                    self.client.get(self.url("records", kind=kind)).status_code, 200
                )
