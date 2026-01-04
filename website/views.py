from django.shortcuts import render, redirect
from .models import Blog, ContactMessage

def home(request):
    blogs = Blog.objects.all().order_by('-date_posted')[:3]
    return render(request, 'website/home.html', {'blogs': blogs})

def blog_list(request):
    all_blogs = Blog.objects.all().order_by('-date_posted')
    return render(request, 'website/blog_list.html', {'blogs': all_blogs})

def contact_view(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            message=request.POST.get('message')
        )
    return redirect('home')