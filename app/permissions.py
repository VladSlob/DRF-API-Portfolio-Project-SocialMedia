from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAuthenticatedReadOnly(BasePermission):
    """
    The request user is authenticated and he is object owner.,
     or request is authenticated as user is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "author"):
            return obj.author == request.user
        if hasattr(obj, "reviewer"):
            return obj.reviewer == request.user
        if hasattr(obj, "follower"):
            return obj.follower == request.user
