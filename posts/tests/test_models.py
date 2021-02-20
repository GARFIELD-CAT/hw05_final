from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        author = User.objects.create(username="TestUser")
        cls.post = Post.objects.create(
            text="Тестовый текст более 15 символов",
            author=author
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            "text": "текст публикации",
            "group": "группа"
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            "text": "Заполните текст поста",
            "group": "Выберите группу для поста"
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_post_str_method(self):
        """Результат вывоза метода __str__ в Post совпадает с ожидаемым."""
        post = PostModelTest.post
        self.assertEqual(post.__str__(), "Тестовый текст ")


class GroupModelTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-group",
            description="Описание тестовой группы"
        )

    def test_group_str_method(self):
        """Результат вывоза метода __str__ в Group совпадает с ожидаемым."""
        group = self.group
        self.assertEqual(group.__str__(), "Тестовая группа")
