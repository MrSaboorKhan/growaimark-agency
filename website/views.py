from django.shortcuts import render

# Create your views here.
from django.shortcuts import render


def home(request):
    return render(request, 'website/home.html')
from .models import Blog

def home(request):
    blogs = Blog.objects.all().order_by('-date_posted')[:3] # Sirf latest 3 blogs
    return render(request, 'website/home.html', {'blogs': blogs})

def blog_list(request):
    all_blogs = Blog.objects.all().order_by('-date_posted')
    return render(request, 'website/blog_list.html', {'blogs': all_blogs})


from django.shortcuts import redirect
from .models import Blog, ContactMessage


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Data save karna
        ContactMessage.objects.create(name=name, email=email, phone=phone, message=message)
        return redirect('home')  # Message bhejte hi home par wapas le jaye