from django.shortcuts import render, redirect
from .models import Blog, ContactMessage # Check karein ke models sahi se import hain
import google.generativeai as genai

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
                # Key check karein: Quotes ke andar space na ho
                genai.configure(api_key="AIzaSyDcL39FK4B_7V_W0aBop38tMa9ckJQ6Q0w")

                # Naya Fast Model
                model = genai.GenerativeModel('gemini-1.5-flash')

                prompt = f"Write a professional SEO meta description for {keyword}. Max 155 characters."
                response = model.generate_content(prompt)

                description = response.text
            except Exception as e:
                # Ye line aapko bataye gi ke masla Key ka hai ya Library ka
                description = f"Technical Detail: {str(e)}"

    return render(request, 'website/meta_tool.html', {'description': description})