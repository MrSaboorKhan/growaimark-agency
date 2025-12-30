from django.shortcuts import render, redirect
from .models import Blog, ContactMessage


# 1. Home Page View
def home(request):
    blogs = Blog.objects.all().order_by('-date_posted')[:3]
    return render(request, 'website/home.html', {'blogs': blogs})


# 2. Blog List Page View
def blog_list(request):
    all_blogs = Blog.objects.all().order_by('-date_posted')
    return render(request, 'website/blog_list.html', {'blogs': all_blogs})


# 3. Contact Form Submission View
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        return redirect('home')

    return redirect('home')