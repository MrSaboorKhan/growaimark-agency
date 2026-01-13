from django.shortcuts import render, redirect
from .models import Blog, ContactMessage # Check karein ke models sahi se import hain

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


def meta_generator(request):
    description = ""
    if request.method == 'POST':
        keyword = request.POST.get('keyword')
        # Yeh logic keyword ko utha kar description banayegi
        description = f"Looking for the best {keyword}? GrowAIMark provides expert solutions to help you dominate the market with {keyword}. Contact us today to learn more!"

    return render(request, 'website/meta_tool.html', {'description': description})