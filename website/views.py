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
                # Yahan apni Google Gemini API Key paste karein
                genai.configure(api_key="AIzaSyDcL39FK4B_7V_W0aBop38tMa9ckJQ6Q0w")

                model = genai.GenerativeModel('gemini-pro')

                # AI ko detailed instruction dena
                prompt = f"Generate a professional, trending 2026 SEO meta description for: {keyword}. Make it high-converting and under 160 characters. Provide only the description text."

                response = model.generate_content(prompt)
                description = response.text
            except Exception as e:
                description = "AI Engine is busy. Please check your API key or try again."

    return render(request, 'website/meta_tool.html', {'description': description})