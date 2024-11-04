from rest_framework.permissions import BasePermission

from backend_plants.jwt_tokens import get_jwt_payload, get_access_token
from backend_plants.models import CustomUser, AdminUser


class IsUser(BasePermission):
    def has_permission(self, request, view):
        token = get_access_token(request)

        if token is None:
            return False

        try:
            payload = get_jwt_payload(token)
        except Exception as e:
            return False

        try:
            # print("CustomUser.objects.get(id=payload['user_id'])", id)    
            user = CustomUser.objects.get(user_id=payload["user_id"])
        
        except Exception as e:
            return False


        return not(user.is_superuser)

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        token = get_access_token(request)

        if token is None:
            return False

        try:
            payload = get_jwt_payload(token)
        except Exception as e:
            return False

        try:
            # print("CustomUser.objects.get(id=payload['user_id'])", id)    
            user = CustomUser.objects.get(user_id=payload["user_id"])
        except CustomUser.DoesNotExist:
            try:
                admin_user = AdminUser.objects.get(admin_id=payload["user_id"])
            except Exception as e:
                return False
            return admin_user.is_active

        return user.is_active


class IsManager(BasePermission):
    def has_permission(self, request, view):
        token = get_access_token(request)

        if token is None:
            return False

        try:
            payload = get_jwt_payload(token)
        except Exception as e:
            return False
        
        try:
            print("/class IsManager payload = ", payload)
            user = CustomUser.objects.get(user_id=payload["user_id"])
            print("/class IsManager user", user)
            # user = AdminUser.objects.get(admin_id=payload["user_id"])
            # print(user.is_superuser)
        except Exception as e:
            print(f"Admin with {user.user_id} does nt ex , perm.IsManager")
            return False
        print("user", user, "is admin =", user.is_superuser)
        return user.is_superuser
    


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator