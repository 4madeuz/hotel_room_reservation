from rest_framework import permissions


class IsOwnerOrAdminPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.user.is_superuser or obj.user == request.user:
            return True
