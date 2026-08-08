# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    context = {
        "page_title": "داشبورد مدیریت",
    }
    return render(request, "dashboard/index.html", context)