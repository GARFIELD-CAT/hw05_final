import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django import forms

from posts.models import Follow, Group, Post
from yatube.settings import MEDIA_ROOT, BASE_DIR

User = get_user_model()

# Создаем временную папку для медиа-файлов.
MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем картинку.
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        # Загружаем картинку.
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
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
            author=PostsPagesTest.author,
            group=PostsPagesTest.group,
            image=PostsPagesTest.uploaded
        )
        cls.form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем авторизованный клиент.
        self.user = User.objects.create(username="TestUserLogged")
        self.authorized_client = Client()
        # Авторизуем пользователя.
        self.authorized_client.force_login(self.user)
        # Создаем клиент автора поста.
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostsPagesTest.post.author)
        # Создаем клиент не подписчика.
        self.user_not_follower = User.objects.create(
            username="TestUserNotFollower"
        )
        self.authorized_client_not_follower = Client()
        self.authorized_client_not_follower.force_login(
            self.user_not_follower
        )
        # Список ожидаемых html-шаблонов и их name.
        self.templates_pages_names = {
            "index.html": reverse("index"),
            "new_post.html": reverse("new_post"),
            "group.html": reverse(
                "group", kwargs={"slug": PostsPagesTest.group.slug}
            ),
            "profile.html": reverse(
                "profile", kwargs={"username": PostsPagesTest.post.author}
            ),
            "post.html": reverse(
                "post",
                kwargs={
                    "username": PostsPagesTest.post.author,
                    "post_id": PostsPagesTest.post.id
                }
            ),
        }
        # Создаем подписку на автора.
        Follow.objects.create(
            user=self.user,
            author=PostsPagesTest.post.author
        )

    # Проверяем корректность вызовов шаблонов.
    def test_pages_uses_correct_template(self):
        """Reverse name используют соответствующий шаблон."""
        templates_pages_names = self.templates_pages_names
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_uses_correct_template(self):
        """Reverse name post_edit использует соответствующий шаблон."""
        # Доступ сюда имеет только автор поста.
        # Отдельный тест из-за одинакового шаблона со страницей создания поста.
        template_post_edit = "new_post.html"
        response = self.authorized_client_author.get(
            reverse(
                "post_edit",
                kwargs={
                    "username": PostsPagesTest.post.author,
                    "post_id": PostsPagesTest.post.id
                }
            )
        )
        self.assertTemplateUsed(response, template_post_edit)

    # Проверяем корректность словарей context в шаблонах.
    def test_new_post_page_show_correct_contex(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("new_post"))
        # Список ожидаемых полей формы.
        form_fields = PostsPagesTest.form_fields

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_contex(self):
        """Шаблон для index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("index"))
        index_text_0 = response.context.get("page")[0].text
        index_author_0 = response.context.get("page")[0].author.username
        index_image_0 = response.context.get("page")[0].image
        self.assertEqual(index_text_0, PostsPagesTest.post.text)
        self.assertEqual(index_author_0, PostsPagesTest.post.author.username)
        self.assertEqual(index_image_0, PostsPagesTest.post.image)

    def test_group_page_show_correct_contex(self):
        """Шаблон для group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "group", kwargs={"slug": PostsPagesTest.group.slug}
            )
        )
        group_description = response.context.get("group").description
        group_title = response.context.get("group").title
        group_post_text_0 = response.context.get("page")[0].text
        group_post_author_0 = response.context.get("page")[0].author.username
        group_post_image_0 = response.context.get("page")[0].image
        self.assertEqual(group_post_text_0, PostsPagesTest.post.text)
        self.assertEqual(
            group_post_author_0, PostsPagesTest.post.author.username
        )
        self.assertEqual(group_post_image_0, PostsPagesTest.post.image)
        self.assertEqual(group_description, PostsPagesTest.group.description)
        self.assertEqual(group_title, PostsPagesTest.group.title)

    def test_profile_page_show_correct_context(self):
        """Шаблон для profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "profile", kwargs={"username": PostsPagesTest.post.author}
            )
        )
        profile_author = response.context.get("author").username
        profile_post_text_0 = response.context.get("page")[0].text
        profile_post_image_0 = response.context.get("page")[0].image
        profile_following = response.context.get("following")
        self.assertEqual(profile_author, PostsPagesTest.post.author.username)
        self.assertEqual(profile_post_text_0, PostsPagesTest.post.text)
        self.assertEqual(profile_post_image_0, PostsPagesTest.post.image)
        # True так как authorized_client подписан на автора поста.
        self.assertEqual(profile_following, True)

    def test_post_page_show_correct_context(self):
        """Шаблон для post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "post",
                kwargs={
                    "username": PostsPagesTest.post.author,
                    "post_id": PostsPagesTest.post.id
                }
            )
        )
        post_author = response.context.get("author").username
        post_text = response.context.get("post").text
        post_image = response.context.get("post").image
        post_following = response.context.get("following")
        self.assertEqual(post_author, PostsPagesTest.post.author.username)
        self.assertEqual(post_text, PostsPagesTest.post.text)
        self.assertEqual(post_image, PostsPagesTest.post.image)
        # True так как authorized_client подписан на автора поста.
        self.assertEqual(post_following, True)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон для post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(
                "post_edit",
                kwargs={
                    "username": PostsPagesTest.post.author,
                    "post_id": PostsPagesTest.post.id
                }
            )
        )
        form_fields = PostsPagesTest.form_fields

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Проверяем появление поста на страницах index и group.
    def test_post_show_on_index_page(self):
        """Пост появляется на главной странице при указании группы."""
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(len(response.context["page"]), 1)
        self.assertEqual(
            response.context.get("page")[0].text, PostsPagesTest.post.text
        )

    def test_post_show_on_group_page(self):
        """Пост появляется на странице выбранной группы."""
        response = self.authorized_client.get(
            reverse(
                "group", kwargs={"slug": PostsPagesTest.group.slug}
            )
        )
        self.assertEqual(
            response.context.get("page")[0].text, PostsPagesTest.post.text
        )
        # Группа с постом.
        self.assertEqual(
            response.context.get("page")[0].group, PostsPagesTest.group
        )

    def test_post_not_showed_on_group_page(self):
        """Пост не появляется на странице другой группы."""
        # Создаем 2 группу без постов.
        group = Group.objects.create(
            title="Тестовая группа 2",
            slug="slug-test-2",
            description="Описание тестовой группы 2"
        )
        response = self.authorized_client.get(
            reverse("group", kwargs={"slug": group.slug})
        )
        with self.assertRaisesMessage(IndexError, "list index out of range"):
            response.context.get("page")[0].text, PostsPagesTest.post.text

    def test_cache_index_page(self):
        """Кэширование страницы index работает"""
        # Делаем запрос до записи нового поста.
        response = self.authorized_client.get(reverse("index"))
        # content содержит тело ответа на запрос.
        cached_response_content = response.content
        # Создаем новый пост.
        Post.objects.create(
            text="Тестовый текст поста 2",
            author=PostsPagesTest.author,
        )
        # Делаем запрос после записи нового поста.
        response = self.authorized_client.get(reverse("index"))
        # Сравниваем контент двух запросов.
        # Если кэш работает, то он не должен измениться.
        self.assertEqual(cached_response_content, response.content)

    # Проверяем функционал подписок.
    def test_authorized_user_can_remove_to_authors_from_subscribe(self):
        """Авторизованный пользователь может удалять других пользователей
        из своих подписок.
        """
        # Считаем количество подписок у пользователя.
        user = self.user
        follower_count = user.follower.count()
        # Отписываемся от автора.
        self.authorized_client.get(
            reverse(
                "profile_unfollow",
                kwargs={"username": PostsPagesTest.post.author}
            )
        )
        # Сравниваем количество подписок у пользователя.
        self.assertEqual(user.follower.count(), follower_count - 1)

    def test_authorized_user_can_add_to_authors_in_subscribe(self):
        """Авторизованный пользователь может подписываться на других
        пользователей.
        """
        # Считаем количество подписок у пользователя.
        user = self.user_not_follower
        follower_count = user.follower.count()
        # Подписываемся на автора.
        self.authorized_client_not_follower.get(
            reverse(
                "profile_follow",
                kwargs={"username": PostsPagesTest.post.author}
            )
        )
        # Сравниваем количество подписок у пользователя.
        self.assertEqual(user.follower.count(), follower_count + 1)

    def test_new_post_show_on_follow_page(self):
        """Новый пост автора показывается на странице подписок у подписчика."""
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(
            response.context.get("page")[0].text, PostsPagesTest.post.text
        )

    def test_new_post_not_showed_on_follow_page_of_an_unsigned_user(self):
        """Новый пост автора не показывается на странице подписок у
        неподписанного пользователя.
        """
        response = self.authorized_client_not_follower.get(
            reverse("follow_index")
        )
        with self.assertRaisesMessage(IndexError, "list index out of range"):
            response.context.get("page")[0].text, PostsPagesTest.post.text


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем автора поста.
        User = get_user_model()
        author = User.objects.create(username="AuthorPost")
        # Создаем тестовую группу в БД.
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="slug-test",
            description="Описание тестовой группы"
        )
        # Создаем тестовые записи постов в БД.
        objs = (
            Post(
                text=f"Тестовый текст поста {i}",
                author=author,
                group=PaginatorViewsTest.group
            )
            for i in range(13)
        )
        Post.objects.bulk_create(objs)

    # Проверяем работу паджинатора на главной странице.
    def test_index_first_page_containse_ten_records(self):
        """Количество постов на первой index странице равно 10"""
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_index_second_page_containse_three_records(self):
        """Количество постов на второй index странице равно 3"""
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get("page").object_list), 3)

    # Проверяем работу паджинатора на странице группы.
    def test_group_first_page_containse_ten_records(self):
        """Количество постов на первой group странице равно 10"""
        response = self.client.get(
            reverse(
                "group",
                kwargs={"slug": PaginatorViewsTest.group.slug}
            )
        )
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_group_second_page_containse_three_records(self):
        """Количество постов на второй group странице равно 3"""
        response = self.client.get(
            reverse(
                "group",
                kwargs={"slug": PaginatorViewsTest.group.slug}
            ) + "?page=2"
        )
        self.assertEqual(len(response.context.get("page").object_list), 3)
