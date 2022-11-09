from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout as exit
from django.http import HttpResponse
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount
from django.contrib.auth.decorators import login_required
from itertools import chain
import random

# Create your views here.
@login_required(login_url='signin')
def index(req):
    user_object = User.objects.get(username = req.user.username)
    user_profile = Profile.objects.get(user = user_object)

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(follower = req.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user = usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    #user suggestions

    all_users = User.objects.all()
    user_following_all = []

    for users in user_following:
        user_list = User.objects.get(username = users.user)
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username = req.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []
    
    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user = ids)
            username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))
    #posts = Post.objects.all()
    return render(req, 'index.html', {'user_profile': user_profile, 'posts': feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list[:4]})

@login_required(login_url='signin')
def like_post(req):
    username = req.user.username
    post_id = req.GET.get('post_id')

    post = Post.objects.get(id = post_id)

    like_filter = LikePost.objects.filter(post_id = post_id, username = username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id = post_id, username = username)
        new_like.save()
        post.no_of_likes = post.no_of_likes + 1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes - 1
        post.save()
        return redirect('/')


def follow(req):
    if req.method == 'POST':
        follower = req.POST['follower']
        user = req.POST['user']

        if FollowersCount.objects.filter(follower = follower, user = user).first():
            delete_follower = FollowersCount.objects.get(follower = follower, user = user)
            delete_follower.delete()
            return redirect('/profile/' + user)
        else:
            new_follower = FollowersCount.objects.create(follower = follower, user = user)
            new_follower.save()
            return redirect('/profile/' + user)
    else:
        return redirect('/')
@login_required(login_url='signin')
def profile(req, pk):
    user_object = User.objects.get(username = pk)
    user_profile = Profile.objects.get(user = user_object)
    user_posts = Post.objects.filter(user = pk)
    user_posts_length = len(user_posts)
    follower = req.user.username
    user = pk
    user_followers = None
    user_following = None
    
    if FollowersCount.objects.filter(follower = follower, user = user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

        user_followers = len(FollowersCount.objects.filter(user = pk))
        user_following = len(FollowersCount.objects.filter(follower = pk))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_posts_length': user_posts_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(req, 'profile.html', context)


@login_required(login_url='signin')
def upload(req):
    if req.method == 'POST':
        user = req.user.username
        image = req.FILES.get('image_upload')
        caption = req.POST['caption']

        new_post = Post.objects.create(user = user, image = image, caption = caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='signin')
def settings(req):
    user_profile = Profile.objects.get(user = req.user)

    if req.method == 'POST':

        if req.FILES.get('image') == None:
            image = user_profile.profileimg
            bio = req.POST['bio']
            location = req.POST['location']

            user_profile.bio = bio
            user_profile.profileimg = image
            user_profile.location = location
            user_profile.save()

        if req.FILES.get('image') != None:
            image = req.FILES.get('image')
            bio = req.POST['bio']
            location = req.POST['location']

            user_profile.bio = bio
            user_profile.profileimg = image
            user_profile.location = location
            user_profile.save()

        return redirect('setting')
    return render(req, 'setting.html', {'user_profile': user_profile})

def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('/signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('/signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                #log user in and redirect to settings page
                user_login = authenticate(username=username, password=password)
                login(request, user_login)

                #create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('/setting')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('/signup')
        
    else:
        return render(request, 'signup.html')

def signin(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print('username ', username, 'password ', password)

        user = authenticate(username=username, password=password)
        print('user ', user)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('/signin')

    else:
        return render(request, 'signin.html')
        
@login_required(login_url='signin')
def logout(req):
    exit(req)
    return redirect('/signin')

@login_required(login_url='signin')
def search(req):
    user_object = User.objects.get(username = req.user.username)
    user_profile = Profile.objects.get(user = user_object)

    if req.method == 'POST':
        username = req.POST['username']
        username_object = User.objects.filter(username__icontains = username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)
        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user = ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))
    return render(req, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})