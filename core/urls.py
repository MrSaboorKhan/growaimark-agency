from django.urls import path
from website import views
urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('contact-submit/', views.contact_view, name='contact_view'),
]