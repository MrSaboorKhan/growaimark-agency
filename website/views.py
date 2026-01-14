from django.shortcuts import render, redirect
from .models import Blog, ContactMessage # Check karein ke models sahi se import hain
import random

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
        keyword = request.POST.get('keyword', '').lower()

        # Latest Trending Templates based on Intent
        templates = {
            "marketing": [
                f"Boost your brand with our data-driven {keyword} strategies. We combine AI insights with expert execution to scale your business. Get a free audit!",
                f"Skyrocket your ROI with premium {keyword} solutions. GrowAIMark delivers trending marketing tactics tailored for 2026 growth. Start today!"
            ],
            "tech": [
                f"Future-proof your business with cutting-edge {keyword} integration. Our AI-first approach ensures seamless performance and scalability. Discover more.",
                f"Experience the next generation of {keyword}. GrowAIMark provides innovative tech solutions to keep you ahead of the digital curve."
            ],
            "default": [
                f"Looking for professional {keyword}? Our expert team at GrowAIMark provides high-impact strategies to help you dominate your local and global market.",
                f"Unlock the full potential of {keyword} with GrowAIMark's proven framework. Tailored solutions for businesses ready to lead in their industry."
            ]
        }

        # Select category based on keyword
        if any(word in keyword for word in ["marketing", "ads", "seo", "social"]):
            category = "marketing"
        elif any(word in keyword for word in ["tech", "web", "app", "software", "ai"]):
            category = "tech"
        else:
            category = "default"

        description = random.choice(templates[category])

    return render(request, 'website/meta_tool.html', {'description': description})