from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Blog

# Is line se aapka Blog section admin panel mein nazar aane lagega
admin.site.register(Blog)

from .models import Blog, ContactMessage # ContactMessage ko bhi import karein

admin.site.register(ContactMessage)