from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import random

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