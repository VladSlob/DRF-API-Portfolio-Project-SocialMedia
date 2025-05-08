from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Model
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.conf import settings

from PIL import Image as PILImage
import uuid
from pathlib import Path


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""

        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model"""

    email = models.EmailField(_("email address"), unique=True)
    following = models.ManyToManyField(
        "self",
        through="Follow",
        through_fields=("follower", "followee"),
        symmetrical=False,
        related_name="followers",
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = UserManager()

    def __str__(self):
        return f"username: {self.username}; email: {self.email}"


def upload_picture(instance: "Profile", filename: str) -> Path:
    filename = (
        f"{slugify(instance.user.email)}-{uuid.uuid4()}"
        + Path(filename).suffix
    )
    return Path("profile_pictures") / Path(filename)


class Profile(models.Model):
    """Profile model"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    picture = models.ImageField(
        blank=True, null=True, upload_to=upload_picture
    )
    bio = models.TextField(blank=True, null=True)


class Follow(models.Model):
    """Model representing user follow relationships."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relation",
    )
    followee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers_relation",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followee"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("followee")),
                name="follower_not_followee",
            ),
        ]

    @staticmethod
    def check_not_me(follower, followee, error):
        """Validate that a user cannot follow themselves."""
        if follower == followee:
            raise error("You cannot follow yourself.")

    def clean(self):
        """Validate Follow instance."""
        self.check_not_me(
            follower=self.follower,
            followee=self.followee,
            error=ValidationError,
        )

    def __str__(self):
        return (
            f"{self.follower.user.username} follows "
            f"{self.followee.user.username}"
        )


class Hashtag(models.Model):
    text = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.text


class Post(models.Model):
    """Post model"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    content = models.TextField()
    hashtags = models.ManyToManyField(
        Hashtag, related_name="posts", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    time_to_publicate = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def validate_post(is_published, time_to_publicate, error):
        """Ensure time_to_publicate is provided if the post is not published."""
        if is_published is False and time_to_publicate is None:
            raise error(
                "Choose a time to_publicate or set is_published = True if you want to publish now."
            )
        if is_published is False and time_to_publicate <= timezone.now():
            raise error("You must set a future time for `time_to_publicate`.")

    def clean(self):
        """Ensure time_to_publicate is in the future and create Celery task"""
        self.validate_post(
            is_published=self.is_published,
            time_to_publicate=self.time_to_publicate,
            error=ValidationError,
        )


def upload_image(instance: "Image", filename: str) -> Path:
    today = timezone.now().strftime("%Y/%m/%d")
    filename = (
        f"{slugify(instance.post)}-{uuid.uuid4()}" + Path(filename).suffix
    )
    return Path(today) / Path(filename)


class Image(models.Model):
    """Image model"""

    picture = models.ImageField(upload_to=upload_image)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="images"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = PILImage.open(self.picture.path)
        if img.height > 1080 or img.width > 1920:
            img.thumbnail((1080, 1920))
            img.save(self.picture.path)


class Comment(models.Model):
    """Feedback model"""

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()

    @staticmethod
    def validate_feedback(
        reviewer: settings.AUTH_USER_MODEL,
        post: Post,
        error: Exception,
    ) -> None:

        if reviewer == post.author:
            raise error("You cannot comment your post")

    ##############замість такої валідації це можна було визначити в constraints,
    # але який підхід кращий?
    def clean(self):
        """Validate Feedback instance."""
        self.validate_feedback(
            reviewer=self.reviewer,
            post=self.post,
            error=ValidationError,
        )


class Like(models.Model):
    """Like model"""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    is_likes = models.BooleanField(default=False)

    class Meta:
        unique_together = ("post", "reviewer")

    @staticmethod
    def validate_like(
        reviewer: settings.AUTH_USER_MODEL,
        post: Post,
        error: Exception,
    ) -> None:
        if reviewer == post.author:
            raise error("You cannot like your post")

    def clean(self):
        """Validate Feedback instance."""
        self.validate_like(
            reviewer=self.reviewer,
            post=self.post,
            error=ValidationError,
        )
