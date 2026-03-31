from flask import Flask, render_template, request, jsonify, session
import stripe
import os
from tools.seo_analyzer import SEOAnalyzer
from tools.keyword_research import KeywordResearch

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Stripe configuration (Free tier ke liye)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')

# Pricing plans
PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'tools': ['SEO Analyzer (3/day)'],
        'searches': 3
    },
    'basic': {
        'name': 'Basic',
        'price': 9.99,
        'tools': ['SEO Analyzer', 'Keyword Research', 'Basic Reports'],
        'searches': 50
    },
    'pro': {
        'name': 'Professional',
        'price': 29.99,
        'tools': ['All Tools', 'Advanced Analytics', 'API Access', 'Priority Support'],
        'searches': 500
    },
    'agency': {
        'name': 'Agency',
        'price': 99.99,
        'tools': ['Unlimited Access', 'White Label', 'Team Accounts', 'Dedicated Support'],
        'searches': 'Unlimited'
    }
}


@app.route('/')
def home():
    return render_template('index.html', plans=PLANS)


@app.route('/api/seo/analyze', methods=['POST'])
def analyze_seo():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL required'}), 400

    analyzer = SEOAnalyzer(url)
    result = analyzer.analyze()
    return jsonify(result)


@app.route('/api/keywords/suggest', methods=['POST'])
def suggest_keywords():
    data = request.json
    keyword = data.get('keyword')

    if not keyword:
        return jsonify({'error': 'Keyword required'}), 400

    research = KeywordResearch(keyword)
    suggestions = research.get_suggestions()
    return jsonify({'success': True, 'keywords': suggestions})


@app.route('/api/pricing')
def get_pricing():
    return jsonify(PLANS)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    plan = data.get('plan')

    if plan not in PLANS:
        return jsonify({'error': 'Invalid plan'}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{PLANS[plan]["name"]} Plan',
                        'description': f'Access to {PLANS[plan]["tools"][0]} and more'
                    },
                    'unit_amount': int(PLANS[plan]['price'] * 100),
                },
                'quantity': 1,
            }],
            mode='subscription' if plan != 'basic' else 'payment',
            success_url='https://growaimark.com/success',
            cancel_url='https://growaimark.com/cancel',
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)