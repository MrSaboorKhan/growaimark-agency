from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Pricing Plans (Sab Free)
PLANS = {
    'free': {
        'name': 'Free Forever',
        'price': 0,
        'daily_limit': 'Unlimited',
        'tools': ['SEO Analyzer', 'Keyword Research', 'Backlink Checker', 'Rank Tracker'],
        'features': ['Unlimited Analyses', 'PDF Reports', 'Email Support']
    }
}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/seo/analyze', methods=['POST'])
def analyze_seo():
    data = request.json
    url = data.get('url', '')

    return jsonify({
        'success': True,
        'url': url,
        'score': 85,
        'title': f'{url} - Website Analysis',
        'meta_description': 'Comprehensive SEO analysis for better rankings',
        'word_count': 500,
        'issues': ['Consider adding more keywords', 'Improve page loading speed', 'Add internal links'],
        'recommendations': ['Write compelling meta descriptions', 'Optimize images', 'Add more content'],
        'message': '✨ Free SEO Tool - No limits!'
    })


@app.route('/api/keywords/suggest', methods=['POST'])
def suggest_keywords():
    data = request.json
    keyword = data.get('keyword', '')

    return jsonify({
        'success': True,
        'keyword': keyword,
        'keywords': [
            {'keyword': f'{keyword} services', 'volume': 1200, 'competition': 'Medium', 'cpc': 2.50},
            {'keyword': f'best {keyword}', 'volume': 850, 'competition': 'High', 'cpc': 3.20},
            {'keyword': f'{keyword} agency Pakistan', 'volume': 450, 'competition': 'Medium', 'cpc': 1.80},
            {'keyword': f'{keyword} tools', 'volume': 620, 'competition': 'Low', 'cpc': 1.20},
            {'keyword': f'affordable {keyword}', 'volume': 380, 'competition': 'Low', 'cpc': 0.90}
        ],
        'message': '🔥 Free Keyword Research - Unlimited!'
    })


@app.route('/api/backlink/analyze', methods=['POST'])
def analyze_backlinks():
    data = request.json
    url = data.get('url', '')

    return jsonify({
        'success': True,
        'url': url,
        'total_backlinks': 1245,
        'referring_domains': 342,
        'dofollow_links': 890,
        'top_backlinks': [
            {'domain': 'example.com', 'authority': 65},
            {'domain': 'blogger.com', 'authority': 72},
            {'domain': 'news.com', 'authority': 58}
        ],
        'message': '🔗 Free Backlink Analysis!'
    })


@app.route('/api/rank/track', methods=['POST'])
def track_rank():
    data = request.json
    keyword = data.get('keyword', '')

    return jsonify({
        'success': True,
        'keyword': keyword,
        'rankings': [
            {'date': 'Day 1', 'position': 25},
            {'date': 'Day 7', 'position': 18},
            {'date': 'Day 14', 'position': 12},
            {'date': 'Day 30', 'position': 8}
        ],
        'trend': 'improving',
        'message': '📈 Free Rank Tracking!'
    })


@app.route('/api/pricing')
def get_pricing():
    return jsonify(PLANS)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)