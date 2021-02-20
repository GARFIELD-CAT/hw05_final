from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

from .models import Follow, Group, Post
from .forms import CommentForm, PostForm

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "group": group,
        "paginator": paginator,
    }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("index")

    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.posts.all()
    paginator = Paginator(post, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    if Follow.objects.filter(user=request.user, author=author):
        following = True
    else:
        following = False
    context = {
        "page": page,
        "post": post,
        "author": author,
        "paginator": paginator,
        "display_add_comment": True,
        "following": following,
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    if Follow.objects.filter(user=request.user, author=author):
        following = True
    else:
        following = False
    context = {
        "post": post,
        "author": author,
        "comments": comments,
        "form": form,
        "following": following
    }
    return render(request, "post.html", context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author == request.user:
        form = PostForm(
            request.POST or None, instance=post, files=request.FILES or None
        )
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect("post", username, post_id)
    else:
        return redirect("post", username, post_id)
    return render(request, "new_post.html", {"form": form, "post": post})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию.
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


# Обработчик создания нового комментария.
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect("post", username, post_id)
    else:
        return redirect("post", username, post_id)


# Подписки пользователя на авторов.
@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "follow.html", context)


# Подписка на автора.
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author is not None:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect("profile", username)


# Отписка от автора.
@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.get(author__username=username, user=request.user)
    if follow is not None:
        follow.delete()
    return redirect("profile", username)
