from django.shortcuts import render, redirect
from .models import Blog, ContactMessage # Check karein ke models sahi se import hain
import openai

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
        keyword = request.POST.get('keyword', '').strip()

        if keyword:
            try:
                # OpenAI API Key Setup
                openai.api_key = 'YOUR_OPENAI_API_KEY'

                # AI ko Instruction dena (Prompt)
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",  # Ya gpt-4 use karein behtar results ke liye
                    messages=[
                        {"role": "system",
                         "content": "You are a professional SEO expert in 2026. Generate a highly detailed, trending, and click-worthy meta description."},
                        {"role": "user",
                         "content": f"Create a professional SEO meta description for the keyword: {keyword}. Keep it under 160 characters and make it sound like a top-tier digital agency."}
                    ]
                )
                # AI ka jawab nikalna
                description = response.choices[0].message.content
            except Exception as e:
                description = f"Error: API Key ki zaroorat hai ya limit khatam ho gayi hai."

    return render(request, 'website/meta_tool.html', {'description': description})