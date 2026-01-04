from django.db import models

# Create your models here.
from django.db import models

class Blog(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default="Marketing")
    excerpt = models.TextField() # Chota sa introduction
    content = models.TextField() # Pura blog post
    author = models.CharField(max_length=100, default="GrowAiMark Team")
    date_posted = models.DateTimeField(auto_now_add=True)
    image_url = models.URLField(blank=True) # Blog ki image ka link

    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    service = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"