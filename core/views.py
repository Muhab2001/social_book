
import random
import re
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout as authLogout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FollowersCount, Profile, Post, LikePost
from itertools import chain
# Create your views here.

@login_required(login_url="signin")
def index(request):
    user_object = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user=user_object);

    user_following_list = [];
    feed = []

    user_following = FollowersCount.objects.filter(follower = request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        ## each followed has multiple posts and not only one
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    ## user suggestions
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username = user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if x not in list(user_following_all)]


    current_user = User.objects.filter(username= request.user.username)

    final_suggestions_list =  [x for x in list(new_suggestions_list) if x not in list(current_user)]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))


    return render(request, "index.html", {"user_profile": user_profile, "posts": feed_list,
    "suggestions_username_profile_list": suggestions_username_profile_list[:4]})

@login_required(login_url="signin")
def settings(request):
    user_profile = Profile.objects.get(user=request.user) ## retrieved globally from django user model
    # print(user_profile)
    if request.method == "POST":

        if request.FILES.get("image") == None:
            image = user_profile.profileimg
            bio = request.POST["bio"]
            location = request.POST["location"]

           
        if request.FILES.get("image") != None:
            image = request.FILES.get("image")
            bio = request.POST["bio"]
            location = request.POST["location"]
            
        user_profile.profileimg = image;
        user_profile.bio = bio;
        user_profile.location = location
        user_profile.save()

        print(image.file)
        return redirect("settings")
    
    return render(request, "setting.html",context= {"user_profile": user_profile})

def signup(request):

    if(request.method == "POST"):
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password == password2:
            if User.objects.filter(email=email).exists():
                 messages.info(request, "Email taken")
                 return redirect("signup")
            elif User.objects.filter(username=username).exists():
                messages.info(request, "User taken")
                return redirect("signup")
            else:
                ## create a django user
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                ## redirect to settings
                user_login = authenticate(username = username, password = password)
                login(request, user_login)
                
                ## get the user object just created
                user_model = User.objects.get(username=username) 
                ## create a corresponding custom profile model
                new_profile = Profile.objects.create(user=user_model, id_user = user_model.id)
                new_profile.save()
                return redirect("settings")
        else:
            messages.info(request, "Password not matching")
            return redirect("signup")
    else:
        return render(request, "signup.html")


def signin(request):

    if(request.method == "POST"):
        username = request.POST["username"]
        
        password = request.POST["password"]
       
        user = authenticate(username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            
            messages.info(request, "Credentials Invalid")
            return redirect("signin")
    else:


        return render(request, "signin.html")


@login_required(login_url="signin")
def logout(request):
    authLogout(request)
    return redirect("signin")

@login_required(login_url="signin")
def upload(request):

    if request.method == "POST":
        user = request.user.username
        image = request.FILES.get("image_upload")
        caption = request.POST["caption"]

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect("/")
    else:
        redirect("/")

@login_required(login_url="signin")
def like_post(request):
    username = request.user.username;
    post_id = request.GET.get("post_id")
    
    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    
    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes += 1;
        post.save()
        print( "New like!" + str(like_filter))
        return redirect("/")
    else:
        print( "Nope!" + str(like_filter))
        like_filter.delete()
        post.no_of_likes -=1
        post.save()
        return redirect("/")

@login_required(login_url="signin")
def profile(request, pk):
    user_obj = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_obj)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    follower = request.user.username;

    user = pk

    if(FollowersCount.objects.filter(follower = follower, user = user).first() != None):
        button_text = "Unfollow"
    else:
        button_text = "follow"

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        "user_object": user_obj,
        "user_profile": user_profile,
        "user_posts": user_posts,
        "user_post_length": user_post_length,
        "button_text": button_text,
        "user_followers": user_followers,
        "user_following": user_following
    }
    return render(request, "profile.html", context=context)

@login_required(login_url="signin")
def follow(request):
    if(request.method == "POST"):
        follower = request.POST["follower"]
        user = request.POST["user"]
        # print(follower, user)
        if FollowersCount.objects.filter(follower=follower, user=user).first() != None:
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect("/profile/" + user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect("/profile/" + user)
    else:
        return redirect("/");

@login_required(login_url="signin")
def search(request):

    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)


    if request.method == "POST":
        username = request.POST["username"]
        username_object = User.objects.filter(username__icontains = username)

        username_profile = []
        username_profile_list = []

        for user in username_object:
            username_profile.append(user.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user = ids).first()
            username_profile_list.append(profile_lists)

        # username_profile_list = list(*chain(*username_profile_list))

    return render(request, "search.html", {"user_profile": user_profile,
    "username_profile_list": username_profile_list})