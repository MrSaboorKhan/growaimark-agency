from django.urls import path
from . import views

urlpatterns = [
    # 1. Main Home Page ka rasta
    path('', views.home, name='home'),

    # 2. Saare Blogs dikhane ka rasta
    path('blog/', views.blog_list, name='blog_list'),

    # 3. Contact Form submit karne ka rasta (Iska name 'contact_view' hona lazmi hai)
    path('contact-submit/', views.contact_view, name='contact_view'),
]