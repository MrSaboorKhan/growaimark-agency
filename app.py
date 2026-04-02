from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import random
from datetime import datetime

app = Flask(__name__)

# ==================== PAGE ROUTES ====================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

# ==================== API ROUTES (Your Tools) ====================
# (Aapke existing API routes yahan honi chahiye)
# ... all your /api/ routes ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

# Load blog posts from JSON file
BLOG_FILE = 'blog_posts.json'


def load_blog_posts():
    try:
        with open(BLOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_blog_posts(posts):
    with open(BLOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


# Blog API Routes
@app.route('/api/blog/posts')
def get_blog_posts():
    posts = load_blog_posts()
    # Return only necessary fields for listing
    return jsonify([{
        'id': p['id'],
        'title': p['title'],
        'slug': p['slug'],
        'category': p['category'],
        'date': p['date'],
        'read_time': p['read_time'],
        'image': p['image'],
        'excerpt': p['excerpt']
    } for p in posts])


@app.route('/api/blog/post/<slug>')
def get_blog_post(slug):
    posts = load_blog_posts()
    for post in posts:
        if post['slug'] == slug:
            return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


@app.route('/api/blog/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    data = request.json
    posts = load_blog_posts()

    for post in posts:
        if post['slug'] == slug:
            comment = {
                'name': data.get('name', 'Anonymous'),
                'text': data.get('text', ''),
                'date': datetime.now().strftime('%B %d, %Y')
            }
            post.setdefault('comments', []).append(comment)
            save_blog_posts(posts)
            return jsonify({'success': True, 'comment': comment})

    return jsonify({'error': 'Post not found'}), 404


# Blog page routes
@app.route('/blog')
def blog_list():
    return render_template('blog.html')


@app.route('/blog/<slug>')
def blog_post(slug):
    return render_template('blog_post.html')