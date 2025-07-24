from django.shortcuts import render


def error_404(request, exception):
    return render(request, "error_pages/404.html", status=404)


def error_500(request):
    return render(request, "error_pages/500.html", status=500)
