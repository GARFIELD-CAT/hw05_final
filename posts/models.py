from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.fields.related import ForeignKey

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        "название группы",
        max_length=200,
        help_text="Заполните название группы"
    )
    slug = models.SlugField(
        "url адрес",
        unique=True,
        help_text="Укажите адрес url для вашей группы на латинском"
    )
    description = models.TextField(
        "описание группы",
        help_text="Заполните описание группы"
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        "текст публикации",
        help_text="Заполните текст поста"
    )
    pub_date = models.DateTimeField(
        "дата публикации",
        auto_now_add=True,
        help_text="Дата формируется автоматически"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="автор",
        help_text="Выберите автора поста"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="группа",
        help_text="Выберите группу для поста"
    )
    image = models.ImageField(
        "картинка публикации",
        upload_to="posts/",
        blank=True,
        null=True,
        help_text="Загрузите картинку"
    )

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="пост",
        help_text="Выберите пост для комментария"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="автор",
        help_text="Укажите автора комментария"
    )
    text = models.TextField(
        "Текст комментария",
        help_text="Заполните текст комментария"
    )
    created = models.DateTimeField(
        "дата публикации",
        auto_now_add=True,
        help_text="Дата формируется автоматически"
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="подписчик",
        help_text="Укажите подписчика"
    )
    author = ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="автор",
        help_text="Выберите автора для подписки"
    )
