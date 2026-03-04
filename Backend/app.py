from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os

# Add tools folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Import our tool
try:
    from seo_tool import analyze_website

    print("✅ SEO Tool imported successfully")
except Exception as e:
    print(f"❌ Error importing SEO tool: {e}")


    def analyze_website(url):
        return {"error": "SEO tool not available"}

app = Flask(__name__, static_folder='../website', static_url_path='')
CORS(app)


@app.route('/')
def serve_home():
    """Serve the homepage"""
    return send_from_directory('../website', 'index.html')


@app.route('/css/<path:path>')
def serve_css(path):
    """Serve CSS files"""
    return send_from_directory('../website/css', path)


@app.route('/js/<path:path>')
def serve_js(path):
    """Serve JS files"""
    return send_from_directory('../website/js', path)


@app.route('/api/seo/analyze', methods=['POST'])
def seo_analyze():
    """API endpoint for SEO analysis"""
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Call our SEO tool
        result = analyze_website(url)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'GrowAIMark API is running'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)