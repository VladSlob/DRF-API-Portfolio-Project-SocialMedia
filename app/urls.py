from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from app.views import (
    CreateUserView,
    LoginUserView,
    LogoutUserView,
    ProfileViewSet,
    FollowViewSet,
    FollowersViewSet,
    MyFollowingSet,
    MyFollowersSet,
    PostViewSet,
    CommentViewSet,
    LikeViewSet,
)

app_name = "app"

router = DefaultRouter()
router.register(r"profile", ProfileViewSet)
router.register(r"follow", FollowViewSet)
router.register(r"following", MyFollowingSet, basename="following")
router.register(r"followers", MyFollowersSet, basename="followers")
router.register(r"post", PostViewSet, basename="post")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"like", LikeViewSet, basename="like")


urlpatterns = [
    path("register/", CreateUserView.as_view(), name="user-register"),
    path("login/", LoginUserView.as_view(), name="take-token"),
    path("logout/", LogoutUserView.as_view(), name="logout"),
    path("", include(router.urls)),
]
