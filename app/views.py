from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404

from rest_framework import viewsets, generics, mixins, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from app.permissions import IsOwnerOrAuthenticatedReadOnly
from app.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    LogoutSerializer,
    ProfileListSerializer,
    ProfileCreateSerializer,
    ProfileDetailSerializer,
    ProfileUpdateSerializer,
    FollowSerializer,
    FollowListSerializer,
    FollowersSerializer,
    MyFollowingSerializer,
    MyFollowersSerializer,
    AllPostsListSerializer,
    PostCreateSerializer,
    MyFollowingPostsListSerializer,
    ImageCreateSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentListSerializer,
    LikeCreateSerializer,
    LikeListSerializer,
    LikeUpdateSerializer,
    LikePostExtraActionSerializer,
)
from app.models import Profile, Follow, Post, Image, Comment, Like


class CreateUserView(generics.CreateAPIView):
    """Endpoint for creating a new user in the system."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class LoginUserView(ObtainAuthToken):
    """Endpoint for logging in."""

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer


class LogoutUserView(APIView):
    """Endpint for logging out the user by deleting their token."""

    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response({"detail": "Successfully logged out."})


class ProfileViewSet(viewsets.ModelViewSet):
    """Endpoint for working with profile data."""

    serializer_class = ProfileCreateSerializer
    queryset = Profile.objects.all().select_related("user")
    permission_classes = (IsOwnerOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "list":
            return ProfileListSerializer
        elif self.action == "retrieve":
            return ProfileDetailSerializer
        elif self.action in ("update", "partial_update"):
            return ProfileUpdateSerializer
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="Filter by user id (ex.?id=2)",
            ),
            OpenApiParameter(
                "username",
                type=OpenApiTypes.STR,
                description="Filter by username (ex.?username=bestuser)",
            ),
            OpenApiParameter(
                "firstname",
                type=OpenApiTypes.STR,
                description="Filter by first name(ex. ?firstname=John)",
            ),
            OpenApiParameter(
                "lastname",
                type=OpenApiTypes.STR,
                description="Filter by last name (ex. ?lastname=Doe)",
            ),
            OpenApiParameter(
                "joined",
                type=OpenApiTypes.STR,
                description="Filter by joined date "
                "(ex. ?joined=YYYY-MM-DD,YYYY-MM-DD)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of profiles."""
        queryset = self.get_queryset()
        if hasattr(self, "extra_context") and self.extra_context.get("errors"):
            return Response(
                {"errors": self.extra_context["errors"]}, status=400
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Return queryset for profiles."""
        errors = {}
        user_id = self.request.query_params.get("user_id")
        username = self.request.query_params.get("username")
        first_name = self.request.query_params.get("firstname")
        last_name = self.request.query_params.get("lastname")
        joined = self.request.query_params.get("joined")

        queryset = self.queryset

        if user_id:
            try:
                user_id = int(user_id)
                return queryset.filter(user_id=user_id)
            except ValueError:
                errors["user_id"] = (
                    "Invalid user ID format. Use integer ?user_id=5"
                )

        if username:
            queryset = queryset.filter(user__username__icontains=username)

        if first_name:
            queryset = queryset.filter(user__first_name__icontains=first_name)

        if last_name:
            queryset = queryset.filter(user__last_name__icontains=last_name)

        if joined:
            try:
                start, end = joined.split(",")
                start = datetime.strptime(start.strip(), "%Y-%m-%d")
                end = datetime.strptime(end.strip(), "%Y-%m-%d")
                return queryset.filter(user__date_joined__range=(start, end))
            except ValueError:
                errors["joined"] = (
                    "Invalid joined format. Use ?joined=YYYY-MM-DD,YYYY-MM-DD"
                )
        self.extra_context = {"errors": errors} if errors else {}
        return queryset


class FollowViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """endpoint for working with follow data."""

    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (IsOwnerOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return FollowListSerializer
        elif self.action == "retrieve":
            return FollowListSerializer
        return self.serializer_class

    def get_queryset(self):
        return self.queryset.filter(follower_id=self.request.user.id)


class FollowersViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """endpoint for working with followers data."""

    queryset = Follow.objects.all()
    serializer_class = FollowersSerializer

    def get_queryset(self):
        return self.queryset.filter(followee_id=self.request.user.id)


class MyFollowingSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """endpoint for working with following data."""

    serializer_class = MyFollowingSerializer
    queryset = get_user_model().objects.all()

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class MyFollowersSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """endpoint for working with my followers data."""

    serializer_class = MyFollowersSerializer
    queryset = get_user_model().objects.all()

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class PostViewSet(viewsets.ModelViewSet):
    """endpoint for working with post data."""

    queryset = (
        Post.objects.all()
        .filter(is_published=True)
        .select_related("author")
        .prefetch_related("hashtags", "images")
    )
    serializer_class = AllPostsListSerializer
    permission_classes = (IsOwnerOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "create":
            return PostCreateSerializer
        elif self.action == "upload_image":
            return ImageCreateSerializer
        elif self.action == "like":
            return LikePostExtraActionSerializer
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                type=OpenApiTypes.STR,
                description="Filter by hashtags (ex. ?tags=tag1,tag2)",
            ),
            OpenApiParameter(
                "author",
                type=OpenApiTypes.STR,
                description="Filter by author (ex. ?author=author)",
            ),
            OpenApiParameter(
                "content",
                type=OpenApiTypes.STR,
                description="Filter by piece of content"
                "(ex. ?content=some text from content)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of posts"""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        tags = self.request.query_params.get("tags")
        author = self.request.query_params.get("author")
        content = self.request.query_params.get("content")
        if tags:
            tags = tags.split(",")
            queryset = queryset.filter(hashtags__text__in=tags)
        if author:
            queryset = queryset.filter(author__username__icontains=author)
        if content:
            queryset = queryset.filter(content__icontains=content)

        return queryset.distinct()

    @action(detail=False, methods=["GET"])
    def my_posts(self, request, *args, **kwargs):
        """Get list of my posts"""
        posts = Post.objects.all().filter(author_id=self.request.user.id)
        serialiser = self.get_serializer(posts, many=True)
        return Response(serialiser.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def my_following(self, request, *args, **kwargs):
        """Get list of my following"""
        posts = Post.objects.all().filter(
            author__in=self.request.user.following.all()
        )
        serialiser = self.get_serializer(posts, many=True)
        return Response(serialiser.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def upload_image(self, request, *args, **kwargs):
        """Upload image for current post"""
        post = self.get_object()
        data = request.data
        data["post"] = post.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def like(self, request, *args, **kwargs):
        """Create like for current post"""
        post = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "post": post},  # як це працює
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def liked(self, request, *args, **kwargs):
        """Get posts that you liked"""
        queryset = self.queryset.filter(
            likes__reviewer=self.request.user.id, likes__is_likes=True
        ).prefetch_related("likes__reviewer")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    """endpoint for working with comment data."""

    queryset = Comment.objects.all()
    serializer_class = CommentListSerializer
    permission_classes = (IsOwnerOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        if self.action in ("update", "partial_update"):
            return CommentUpdateSerializer
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "post",
                type=OpenApiTypes.INT,
                description="Filter by post id (ex. ?post=3)",
            ),
            OpenApiParameter(
                "reviewer_id",
                type=OpenApiTypes.INT,
                description="Filter by reviewer id (ex. ?reviewer=2)",
            ),
            OpenApiParameter(
                "reviewer",
                type=OpenApiTypes.STR,
                description="Filter by reviewer username"
                " (ex. ?reviewer=username)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of comments"""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        post = self.request.query_params.get("post")
        reviwer_id = self.request.query_params.get("reviwer_id")
        reviwer = self.request.query_params.get("reviwer")
        if post:
            queryset = queryset.filter(post_id=int(post))
        if reviwer_id:
            queryset = queryset.filter(reviwer_id=int(reviwer_id))
        if reviwer:
            queryset = queryset.filter(reviewer__username__icontains=reviwer)
        return queryset


class LikeViewSet(viewsets.ModelViewSet):
    """endpoint for working with like data."""

    queryset = Like.objects.all()
    serializer_class = LikeListSerializer
    permission_classes = (IsOwnerOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "create":
            return LikeCreateSerializer
        if self.action in ("update", "partial_update"):
            return LikeUpdateSerializer
        return self.serializer_class
