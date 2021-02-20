from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        # Создание неавторизованный клиент.
        self.guest_client = Client()
        self.templates_url_names = {
            "about/author.html": "/about/author/",
            "about/tech.html": "/about/tech/"
        }

    def test_author_url_exists_at_desired_location(self):
        """Страница /about/author/ доступна анонимному пользователю."""
        response = self.guest_client.get("/about/author/")
        self.assertEqual(response.status_code, 200)

    def test_tech_url_exists_at_desired_location(self):
        """Страница /about/tech/ доступна анонимному пользователю."""
        response = self.guest_client.get("/about/tech/")
        self.assertEqual(response.status_code, 200)

    def test_url_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_url_names = self.templates_url_names
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
