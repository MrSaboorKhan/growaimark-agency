from django.contrib import admin
from django.urls import path, include
from website import views  # <--- YEH LINE SABSE ZAROORI HAI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('contact-submit/', views.contact_view, name='contact_view'),
]