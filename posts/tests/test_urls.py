from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем автора поста.
        cls.author = User.objects.create(username="AuthorPost")
        # Создаем тестовую группу в БД.
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="slug-test",
            description="Описание тестовой группы"
        )
        # Создаем тестовую запись поста в БД.
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=PostsURLTests.author,
            group=PostsURLTests.group
        )

    def setUp(self):
        # Создание неавторизованный клиент.
        self.guest_client = Client()
        # Создаем второй авторизованный клиент.
        self.user = User.objects.create(username="TestUser")
        self.authorized_client = Client()
        # Авторизуем пользователя.
        self.authorized_client.force_login(self.user)
        # Создаем третий клиент автора поста.
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostsURLTests.post.author)

        # Создаем словарь шаблонов и URL адресов.
        self.templates_url_names = {
            "index.html": "/",
            "new_post.html": "/new/",
            "group.html": f"/group/{PostsURLTests.group.slug}/",
            "profile.html": f"/{PostsURLTests.author}/",
            "post.html": f"/{PostsURLTests.author}/{PostsURLTests.post.id}/",
            "misc/404.html": "page-not-found"
        }

    # Проверяем доступность страниц для неавторизованного пользователя.
    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна анонимному пользователю."""
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_group_posts_url_exists_at_desired_location(self):
        """Страница /group/<slug:slug>/ доступна анонимному пользователю."""
        response = self.guest_client.get(f"/group/{PostsURLTests.group.slug}/")
        self.assertEqual(response.status_code, 200)

    # Проверяем доступность страниц для авторизованного пользователя.
    def test_new_post_url_exists_at_desired_location_authorized(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/new/")
        self.assertEqual(response.status_code, 200)

    def test_username_url_exists_at_desired_location_authorized(self):
        """Страница /<username>/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(f"/{PostsURLTests.author}/")
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_url_exists_at_desired_location_authorized(self):
        """Страница /<username>/<post_id>/доступна
        авторизованному пользователю.
        """
        response = self.authorized_client.get(
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/"
        )
        self.assertEqual(response.status_code, 200)

    # Проверяем доступность страницы редактирования поста для его автора.
    def test_post_id_edit_url_exists_at_desired_location_author(self):
        """Страница /<username>/<post_id>/edit/ доступна
        автору поста.
        """
        response = self.authorized_client_author.get(
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/edit/"
        )
        self.assertEqual(response.status_code, 200)

    # Проверяем редиректы для неавторизованного пользователя.
    def test_new_post_url_redirect_anonymous(self):
        """Страница по адресу /new/ перенаправит неавторизованного
        пользователя на страницу логина.
        """
        response = self.guest_client.get("/new/")
        self.assertRedirects(response, "/auth/login/?next=/new/")

    def test_username_post_id_edit_redirect_anonymous(self):
        """Страница /<username>/<post_id>/edit перенаправит неавторизованного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/edit/"
        )
        self.assertRedirects(
            response,
            f"/auth/login/?next="
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/edit/"
        )

    # Проверяем редиректы для не автора поста.
    def test_username_post_id_edit_redirect_not_author(self):
        """Страница /<username>/<post_id>/edit перенаправит не автора поста
        на страницу просмотра поста.
        """
        response = self.authorized_client.get(
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/edit/"
        )
        self.assertRedirects(
            response,
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/"
        )

    # Проверка вызываемых шаблонов для каждого URL адреса.
    def test_url_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_url_names = self.templates_url_names
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    # Отдельный тест, так как одинаковый шаблон
    # используется для создания и редактирования поста.
    def test_post_edit_url_uses_correct_template(self):
        """Страница /<username>/<post_id>/edit использует правильный шаблон."""
        template = "new_post.html"
        response = self.authorized_client_author.get(
            f"/{PostsURLTests.author}/{PostsURLTests.post.id}/edit/"
        )
        self.assertTemplateUsed(response, template)

    def test_page_not_found_exsist(self):
        """Сервер возвращает код 404, если страница не найдена"""
        response = self.authorized_client.get("page-not-found")
        self.assertEqual(response.status_code, 404)
