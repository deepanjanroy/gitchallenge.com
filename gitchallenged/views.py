from django.contrib.auth import login as login_user
from django.contrib.auth import logout as logout_user
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
import requests

from gitchallenged import conf
from gitchallenged.models import UserProfile


def home(request):
    if request.user.is_authenticated():
        context = {
            'profile': request.user.get_profile(),
        }
        return render(request, 'dashboard.html', context)
    else:
        context = {
            'client_id': conf.CLIENT_ID,
        }

        return render(request, 'home.html', context)


def logout(request):
    logout_user(request)
    return redirect('home')


def login(request):
    return render(request, 'home.html')


def authorise(request):
    code = request.GET.get('code')
    if not code:
        raise PermissionDenied

    # Otherwise, use this code to get an access token from GitHub using OAuth
    login_url = 'https://github.com/login/oauth/access_token'
    login_response = requests.post(login_url, data={
        'client_id': conf.CLIENT_ID,
        'client_secret': conf.CLIENT_SECRET,
        'code': code,
    })
    access_token = login_response.text

    # Get some basic data about this user (username, first name, last name)
    # Eventually needs to check that the token is still valid each time
    user_url = 'https://api.github.com/user?%s' % access_token
    user_response = requests.get(user_url)
    user_data = user_response.json()

    # Create a user for this person (if one doesn't exist already) and add the
    # the access token to the user's profile
    print user_data
    username = user_data['login']
    gravatar = user_data['gravatar_id']
    name = user_data['name']
    user, created = User.objects.get_or_create(username=username, password='')
    profile = user.get_profile()
    profile.access_token = access_token
    profile.gravatar = gravatar
    profile.name = name
    profile.save()

    user = authenticate(username=username)
    login_user(request, user)

    return redirect('home')