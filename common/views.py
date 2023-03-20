from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.template.response import TemplateResponse


@login_required
def index(request):

    t_username = request.user.username
    t_user_last_name = request.user.last_name
    t_user_first_name = request.user.first_name
    t_user_is_superuser = request.user.is_superuser

    data = {
        'user_name': t_username,
        'user_first_name': t_user_first_name,
        'user_last_name': t_user_last_name,
        't_user_is_superuser': t_user_is_superuser
    }

    # return render(request, 'top_page.html', data)
    return TemplateResponse(request, 'top_page.html', data)