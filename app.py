from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from werkzeug.utils import secure_filename
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


# Admin Routes
@app.route('/admin')
def admin_panel():
    return render_template('admin.html')


# Get single post by ID (for editing)
@app.route('/api/blog/post/<int:post_id>')
def get_blog_post_by_id(post_id):
    posts = load_blog_posts()
    for post in posts:
        if post['id'] == post_id:
            return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


# Save post (create or update)
@app.route('/api/blog/post/save', methods=['POST'])
def save_blog_post():
    data = request.json
    posts = load_blog_posts()

    if data.get('id'):
        # Update existing post
        for i, post in enumerate(posts):
            if post['id'] == data['id']:
                data['comments'] = post.get('comments', [])
                posts[i] = data
                break
    else:
        # Create new post
        new_id = max([p['id'] for p in posts], default=0) + 1
        data['id'] = new_id
        data['comments'] = []
        posts.append(data)

    save_blog_posts(posts)
    return jsonify({'success': True, 'id': data['id']})


# Delete post
@app.route('/api/blog/post/<int:post_id>/delete', methods=['DELETE'])
def delete_blog_post(post_id):
    posts = load_blog_posts()
    posts = [p for p in posts if p['id'] != post_id]
    save_blog_posts(posts)
    return jsonify({'success': True})


# Get all posts (for listing)
@app.route('/api/blog/posts')
def get_blog_posts():
    posts = load_blog_posts()
    return jsonify([{
        'id': p['id'],
        'title': p['title'],
        'slug': p['slug'],
        'category': p['category'],
        'date': p['date'],
        'read_time': p.get('read_time', '5 min read'),
        'image': p.get('image', 'newspaper'),
        'excerpt': p['excerpt']
    } for p in posts])


# Get single post by slug (for public view)
@app.route('/api/blog/post/<slug>')
def get_blog_post_by_slug(slug):
    posts = load_blog_posts()
    for post in posts:
        if post['slug'] == slug:
            return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


# Add comment
@app.route('/api/blog/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    data = request.json
    posts = load_blog_posts()

    for post in posts:
        if post['slug'] == slug:
            comment = {
                'name': data.get('name', 'Reader'),
                'text': data.get('text', ''),
                'date': datetime.now().strftime('%B %d, %Y')
            }
            post.setdefault('comments', []).append(comment)
            save_blog_posts(posts)
            return jsonify({'success': True})

    return jsonify({'error': 'Post not found'}), 404


# Blog page routes
@app.route('/blog')
def blog_list():
    return render_template('blog.html')


@app.route('/blog/<slug>')
def blog_post(slug):
    return render_template('blog_post.html')


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/blog/upload-image', methods=['POST'])
def upload_blog_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to avoid duplicates
        name, ext = os.path.splitext(filename)
        filename = f"{int(datetime.now().timestamp())}_{name}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        image_url = f"/static/uploads/{filename}"
        return jsonify({'success': True, 'url': image_url})

    return jsonify({'error': 'Invalid file type'}), 400