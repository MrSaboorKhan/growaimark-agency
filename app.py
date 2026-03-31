from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/seo/analyze', methods=['POST'])
def analyze_seo():
    data = request.json
    url = data.get('url', '')
    return jsonify({
        'success': True,
        'url': url,
        'score': 85,
        'title': 'Website Analysis',
        'issues': ['Add meta description'],
        'recommendations': ['Write compelling title']
    })

@app.route('/api/keywords/suggest', methods=['POST'])
def suggest_keywords():
    data = request.json
    keyword = data.get('keyword', '')
    return jsonify({
        'success': True,
        'keywords': [
            {'keyword': f'{keyword} services', 'volume': 1200, 'competition': 'Medium', 'cpc': 2.50},
            {'keyword': f'best {keyword}', 'volume': 800, 'competition': 'High', 'cpc': 3.20}
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)