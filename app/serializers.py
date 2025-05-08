from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator

from app.models import *
from app.tasks import publish_post


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "is_staff",
        )
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "style": {"input_type": "password"},
            }
        }

    def create(self, validated_data):
        """Create and return a new `User` instance, given the validated data."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return an `User` instance, given the validated data."""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for authenticating requests with"""

    email = serializers.CharField(label=_("Email"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                email=email,
                password=password,
            )
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    pass


class ProfileCreateSerializer(serializers.ModelSerializer):
    """Profile create Serializer"""

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
        # validators=[
        #     UniqueValidator(
        #         queryset=get_user_model().objects.all(),
        #         message="A user with that username already exists.",
        #     )
        # ],
        ###############чому не працює?
    )

    class Meta:
        model = Profile
        fields = ("user", "picture", "bio")
        read_only_fields = ("user",)  # is it need? Can we put another user
        # exept defoult wihout this option?

    def validate(self, data):
        user = data.get("user") or self.context["request"].user

        if Profile.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return data


class ProfileListSerializer(serializers.ModelSerializer):
    """Profile list Serializer"""

    user = serializers.StringRelatedField(many=False, read_only=True)
    picture = serializers.URLField(read_only=True)
    bio = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = ("user", "picture", "bio")


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Profile detail Serializer"""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", read_only=True
    )
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    picture = serializers.URLField(read_only=True)
    bio = serializers.CharField(read_only=True)
    joined = serializers.DateTimeField(
        source="user.date_joined", read_only=True
    )

    class Meta:
        model = Profile
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "picture",
            "bio",
            "joined",
        )


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Profile Update Serializer"""

    class Meta:
        model = Profile
        fields = ("picture", "bio")


class FollowSerializer(serializers.ModelSerializer):
    """Add Following Serializer"""

    follower = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Follow
        fields = ("id", "follower", "followee")

    def validate(self, data):
        Follow.check_not_me(
            follower=data["follower"],
            followee=data["followee"],
            error=serializers.ValidationError,
        )
        return data


class FollowListSerializer(serializers.ModelSerializer):
    """Following List Serializer"""

    follower = serializers.StringRelatedField(many=False, read_only=True)
    followee = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "follower", "followee")


class FollowersSerializer(serializers.ModelSerializer):
    """Followers Serializer"""

    follower = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "follower")


class MyFollowingSerializer(serializers.ModelSerializer):
    """My Following Serializer"""

    following = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("following",)


class MyFollowersSerializer(serializers.ModelSerializer):
    """MyFollowers Serializer"""

    followers = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("followers",)


class ImageCreateSerializer(serializers.ModelSerializer):
    """Image Create Serializer for post extra action"""

    class Meta:
        model = Image
        fields = (
            "post",
            "picture",
        )

    def validate(self, data):
        post = data["post"]
        if self.context["request"].user != post.author:
            raise serializers.ValidationError(
                {"post": "You are not the author of this post."}
            )
        return data


class ImageSerializer(serializers.Serializer):
    """Image Serializer, uses in AllPostsListSerializer"""

    picture = serializers.ImageField()


class HashtagSerializer(serializers.Serializer):
    """Hashtag Serializer"""

    text = serializers.CharField()


class AllPostsListSerializer(serializers.ModelSerializer):
    """Post Serializer"""

    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True, many=False
    )
    images = ImageSerializer(many=True, required=False)
    hashtags = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="text"
    )

    class Meta:
        model = Post
        fields = ("id", "author", "content", "hashtags", "images")


class PostCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    images = serializers.ImageField(required=False)
    hashtags = HashtagSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "images",
            "hashtags",
            "is_published",
            "time_to_publicate",
        )

    def create(self, validated_data):
        """create and return a new `Post` instance, given the validated
        data, if added create new `Image` instance, new `Hashtag` instance"""
        with transaction.atomic():
            image_data = validated_data.pop("images", [])
            hashtags_data = validated_data.pop("hashtags", [])
            is_published = validated_data.get("is_published")
            time_to_publicate = validated_data.get("time_to_publicate")
            post = Post.objects.create(**validated_data)
            if image_data:
                Image.objects.create(post=post, picture=image_data)
            if hashtags_data:
                for hashtag_data in hashtags_data:
                    hashtag, created = Hashtag.objects.get_or_create(
                        text=hashtag_data["text"]
                    )
                    post.hashtags.add(hashtag)
            if is_published is False and time_to_publicate:
                publish_post.apply_async(
                    (post.id,), eta=post.time_to_publicate
                )
            return post

    def validate_hashtags(self, value):
        return value

    def validate(self, attrs):
        data = super(PostCreateSerializer, self).validate(attrs)
        is_published = data.get("is_published")
        time_to_publicate = data.get("time_to_publicate")
        Post.validate_post(
            is_published=is_published,
            time_to_publicate=time_to_publicate,
            error=serializers.ValidationError,
        )
        return data


class MyFollowingPostsListSerializer(serializers.ModelSerializer):
    """Post Serializer"""

    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True, many=False
    )
    images = ImageSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ("id", "author", "content", "images")


class CommentCreateSerializer(serializers.ModelSerializer):
    """Comment create Serializer"""

    reviewer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ("reviewer", "post", "content")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["post"].default = self.context.get("post")

    def validate(self, attrs):
        data = super(CommentCreateSerializer, self).validate(attrs)
        reviewer = data.get("reviewer")
        post = data.get("post")
        Comment.validate_feedback(
            reviewer=reviewer,
            post=post,
            error=serializers.ValidationError,
        )
        return data


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Comment update Serializer"""

    class Meta:
        model = Comment
        fields = ("reviewer", "post", "content")
        read_only_fields = ("reviewer", "post")


class CommentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ("id", "reviewer", "content", "post")


class LikeCreateSerializer(serializers.ModelSerializer):
    reviewer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Like
        fields = ("post", "reviewer", "is_likes")


class LikeListSerializer(serializers.ModelSerializer):
    """Like List Serializer"""

    class Meta:
        model = Like
        fields = ("post", "reviewer", "is_likes")


class LikeUpdateSerializer(serializers.ModelSerializer):
    """Like update Serializer"""

    class Meta:
        model = Like
        fields = ("post", "reviewer", "is_likes")
        read_only_fields = ("reviewer", "post")


class LikePostExtraActionSerializer(serializers.ModelSerializer):
    """Like post serialiser for extra action"""

    reviewer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    post = serializers.HiddenField(default=None)

    class Meta:
        model = Like
        fields = ("post", "reviewer", "is_likes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Автоматично встановлюємо поточний пост із контексту
        self.fields["post"].default = self.context.get("post")

    def validate(self, attrs):
        data = super(LikePostSerializer, self).validate(attrs)
        reviewer = data.get("reviewer")
        post = data.get("post")
        Like.validate_like(
            reviewer=reviewer,
            post=post,
            error=serializers.ValidationError,
        )
        return data
