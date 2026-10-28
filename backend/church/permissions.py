from rest_framework.permissions import SAFE_METHODS, BasePermission, DjangoModelPermissions


def is_staff(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff and user.is_active)


class ReadOnlyOrStaffWithModelPermissions(BasePermission):
    """
    Anyone may read (the views decide WHICH records anonymous visitors see).
    Creating, changing or deleting requires a signed-in, active staff account
    that also holds Django's add/change/delete permission for that model.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not is_staff(request):
            return False
        return DjangoModelPermissions().has_permission(request, view)
