import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post
from yatube.settings import MEDIA_ROOT, BASE_DIR

User = get_user_model()

# Создаем временную папку для медиа-файлов.
MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        cls.author = User.objects.create(username="TestAuthor")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="slug-test",
            description="Тестовое описание группы"
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=PostCreateFormTests.author,
            group=PostCreateFormTests.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем авторизованного пользователя.
        self.user = User.objects.create(username="TestUser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает новый пост в базе"""
        post_count = Post.objects.count()
        form_data = {
            "group": PostCreateFormTests.group.id,
            "text": "Тестовый пост_2",
            "image": PostCreateFormTests.uploaded
        }
        # Отправляем POST-запрос.
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект.
        self.assertRedirects(response, reverse("index"))
        # Проверяем, увеличилось ли число постов.
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создалась запись с нашим текстом.
        self.assertTrue(
            Post.objects.filter(text=form_data["text"]).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует пост в базе"""
        # Создаем вторую запись поста в БД.
        post = Post.objects.create(
            text="Тестовый пост 2",
            author=PostCreateFormTests.author,
            group=PostCreateFormTests.group
        )
        form_data = {"text": "Редактированный тестовый пост."}
        # Доступ к странице редактирования поста имеет только автор.
        username = PostCreateFormTests.post.author
        self.authorized_client.force_login(username)
        self.authorized_client.post(
            reverse(
                "post_edit",
                kwargs={"username": username, "post_id": post.id}
            ),
            data=form_data,
            follow=True
        )
        # Пост с отредактированным текстом появился.
        self.assertTrue(
            Post.objects.filter(text=form_data["text"]).exists()
        )
        # Поста с текстом до редактирования нет.
        self.assertFalse(
            Post.objects.filter(text=post.text).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username="TestAuthor")
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=CommentCreateFormTests.author,
        )

    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает новый коммент в базе"""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "Тестовый комментарий"
        }
        # Отправляем POST-запрос.
        response = self.authorized_client.post(
            reverse(
                "add_comment",
                kwargs={
                    "username": CommentCreateFormTests.post.author,
                    "post_id": CommentCreateFormTests.post.id
                }
            ),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект.
        self.assertRedirects(
            response,
            reverse(
                "post",
                kwargs={
                    "username": CommentCreateFormTests.post.author,
                    "post_id": CommentCreateFormTests.post.id
                }
            )
        )
        # Проверяем, увеличилось ли число комментариев.
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        # Проверяем, что создался комментарий с нашим текстом.
        self.assertTrue(
            Comment.objects.filter(text=form_data["text"]).exists()
        )
