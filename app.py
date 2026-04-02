from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

# ========== FORCE SITEMAP ROUTE ==========
@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml from root directory"""
    try:
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml', mimetype='application/xml')
    except Exception as e:
        return f"Error: {e}", 404

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/')
def home():
    return render_template('index.html')