from functools import wraps

from django.http import HttpResponseForbidden

from .models import User


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required.")
        if request.user.role != User.Role.ADMIN or not request.user.household_id:
            return HttpResponseForbidden("Only household admins can perform this action.")
        return view_func(request, *args, **kwargs)

    return wrapped
