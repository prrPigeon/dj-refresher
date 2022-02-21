from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm

# for chaining different filter functionality with and, or etc...
from django.db.models import Q

from .models import Room, Topic, Message
from .forms import RoomForm


def login_user(request):
    
    page = 'login'
    
    if request.user.is_authenticated:
        return redirect('home')
    
    # user_login_form is default check the docs
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except: 
            messages.error(request, "User does not exist")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Wellcome {username}")
            return redirect('home')
        else:
            messages.error(request, 'Username or password is incorrect')
        
    context = {
        'page': page
    }
    return render(request, 'base/login_register.html', context)
    
    
def logout_user(request):
    logout(request)
    return redirect('home')


def register_user(request):
    # page = 'register'
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, 'You are successfully created account.')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Something is wrong with pass or username!!!')
    context = {
        'form': form
    }
    return render(request, 'base/login_register.html', context)
    

def home(request):
    # if request.GET.get('q') != None:
    #     q = request.GET.get('q')
    # else:
    #     q = ''
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    
    activity_messages = Message.objects.all()
    
    topics = Topic.objects.all()
    # count() works faster then len()
    room_count = rooms.count()
    
    context = {
        "rooms": rooms,
        "topics": topics,
        "room_count": room_count,
        "activity_messages": activity_messages
        }
    return render(request, "base/home.html", context)


def room(request, pk):
    # room = None
    # for i in rooms:
    #     if i['id'] == int(pk):
    #         room = i
    room = Room.objects.get(id=pk)
    
    # message_set is child object of Room, Messages in this case, write as lover case
    room_messages = room.message_set.all() #.order_by('-created_at') # we don't need order_by, you fixed the class
    
    participants =  room.participants.all()
    
    if request.method == 'POST':
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        
        # automaticly add user to participants, when he create comment
        # there is more methods accept add(), remove() etc.
        
        room.participants.add(request.user)
        
        # with second arg we asure to full page is reloaded with get request
        # with caution to not mess up something
        return redirect('room', pk=room.id)
    
    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants
        }
    return render(request, "base/room.html", context)


@login_required(login_url=("login"))
def create_room(request):
    form = RoomForm()
    if request.method == 'POST':
        # you can extract all by hand like:
        # request.POST.get('name') do this when you manually create form
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {"form": form }
    return render(request, "base/room_form.html", context)


@login_required(login_url=("login"))
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    if request.user != room.host:
        messages.error(request, 'You cannot update room which you did not create!!!')
        return redirect('login')
    else:
        ...
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid:
            form.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url=("login"))
def delete_room(request, pk):
    room = Room.objects.get(id=pk)
    if request.method == 'POST' and request.user == room.host:
        room.delete()
        messages.success(request, 'You are successfully deleted room')
        return redirect('home')
    context = {'object': room }
    return render(request, 'base/delete.html', context)


@login_required(login_url=("login"))
def delete_message(request, pk):
    message = Message.objects.get(id=pk)
    if request.method == 'POST' and request.user == message.user:
        message.delete()
        messages.success(request, 'You are successfully deleted meessage')
        return redirect('home')
    context = {'object': message }
    return render(request, 'base/delete.html', context)