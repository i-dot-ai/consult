from django.contrib.admin.views.decorators import staff_member_required


def support_login_required(view_func=None):
    actual_decorator = staff_member_required(login_url="/")
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator
