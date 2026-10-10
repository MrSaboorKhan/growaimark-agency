from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import html
import random
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from ai_helper import ask_gemini, check_rate_limit, get_client_ip, AIError
from tool_seo import seo_bp

app = Flask(__name__)
app.register_blueprint(seo_bp)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# ==================== CONFIGURATION ====================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== TRANSLATOR TOOL IMPORT ====================
try:
    from tools.video_translator import VideoTranslator

    translator = VideoTranslator()
    print("✅ Video Translator imported successfully")
except ImportError as e:
    print(f"⚠️ Video Translator import failed: {e}")
    translator = None


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


@app.route('/admin')
def admin_panel():
    return render_template('admin.html')


@app.route('/blog/<slug>')
def blog_post(slug):
    return render_template('blog_post.html')


@app.route('/translator')
def translator_page():
    """Translator tool page"""
    if translator is None:
        return "Translator tool is currently unavailable. Please check back later.", 503
    return render_template('translator.html')


# ==================== AI CONTENT GENERATOR (Gemini) ====================
CONTENT_TASKS = {
    'blog': (
        "Write a helpful, well-structured blog post about: {topic}.\n"
        "Length: about 600 to 800 words. Put a catchy title on the first line. Then write an introduction, "
        "4 or 5 sections (each heading on its own line in CAPITAL LETTERS), practical tips with simple examples, "
        "and a short conclusion with a call to action."
    ),
    'social': (
        "Write 3 different social media posts about: {topic}.\n"
        "Label them POST 1, POST 2 and POST 3. Each post needs a strong first line (hook), 2 to 4 short lines of value, "
        "a call to action, and 5 to 8 relevant hashtags. Use a few fitting emojis."
    ),
    'email': (
        "Write a marketing email newsletter about: {topic}.\n"
        "Start with 3 subject line options (label them SUBJECT 1, 2, 3). Then write the email: a friendly greeting, "
        "a short engaging opening, 3 clear value points, one call to action, and a sign-off from the GrowAIMark team."
    ),
    'ad': (
        "Write ad copy for: {topic}.\n"
        "Give 3 Facebook/Instagram ad variations (each with Headline, Primary Text and Call to Action) "
        "and 3 Google Search ads (each with 2 headlines of max 30 characters and 1 description of max 90 characters). "
        "Label every variation clearly."
    ),
}

CONTENT_SYSTEM = (
    "You are an expert digital marketing copywriter. Write clear, natural, persuasive content in a {tone} tone, "
    "in {language}. Output PLAIN TEXT only: no markdown symbols (no ** and no #) and no HTML tags. "
    "Never invent statistics, percentages, client names, awards or guarantees. "
    "Give only the finished content, without any introduction like 'Here is your post'."
)


@app.route('/api/content/generate', methods=['POST'])
def generate_content():
    data = request.get_json(silent=True) or {}
    topic = str(data.get('topic', '')).strip()
    content_type = str(data.get('type', 'blog')).strip().lower()
    tone = str(data.get('tone', 'professional')).strip()[:30] or 'professional'
    language = str(data.get('language', 'English')).strip()[:30] or 'English'

    if not topic:
        return jsonify({'error': 'Topic is required', 'content': 'Please enter a topic.',
                        'message': 'Topic is required'}), 400
    if len(topic) > 200:
        return jsonify({'error': 'Topic is too long', 'content': 'Please keep the topic under 200 characters.',
                        'message': 'Topic is too long'}), 400

    if content_type not in CONTENT_TASKS:
        content_type = 'ad' if content_type == 'ad copy' else 'blog'

    try:
        check_rate_limit(get_client_ip(request))
        text = ask_gemini(
            CONTENT_TASKS[content_type].format(topic=topic),
            system=CONTENT_SYSTEM.format(tone=tone, language=language),
            temperature=0.8,
            max_tokens=4096,
        )
    except AIError as e:
        return jsonify({'error': e.message, 'content': e.message, 'message': 'Something went wrong'}), e.status
    except Exception as e:
        print(f"[AI] Unexpected error in content generator: {e}")
        msg = 'Something went wrong. Please try again.'
        return jsonify({'error': msg, 'content': msg, 'message': msg}), 500

    # HTML escape: AI ka text page par safely dikhane ke liye
    safe_text = html.escape(text)

    return jsonify({
        'success': True,
        'topic': topic,
        'type': content_type,
        'content': safe_text,
        'word_count': len(text.split()),
        'message': 'AI Content Generated Successfully!'
    })


# ==================== YOUTUBE SEO OPTIMIZER ====================
@app.route('/api/youtube/seo', methods=['POST'])
def youtube_seo():
    try:
        data = request.json
        title = data.get('title', '')

        if not title:
            return jsonify({'error': 'Video title is required'}), 400

        optimized_titles = [
            f"{title} - Complete Guide 2024",
            f"How to {title} Like a Pro (Step by Step)",
            f"{title} Tutorial: Beginner to Advanced",
            f"Best {title} Tips You Need to Know",
            f"{title} for Beginners - Full Course",
            f"{title}: The Ultimate Guide",
            f"Top 10 {title} Strategies That Work"
        ]

        tags = [
            title.lower(),
            f"{title.lower()} tutorial",
            f"{title.lower()} guide",
            "digital marketing",
            "SEO tips",
            "marketing strategy",
            "business growth",
            "online marketing",
            "social media marketing"
        ]

        optimized_desc = f"""{title} - Complete Guide 2024

📌 In this video, you'll learn:
✅ What is {title}
✅ Why it matters for your business
✅ Step-by-step implementation
✅ Common mistakes to avoid
✅ Pro tips for better results

⏰ Timestamps:
0:00 - Introduction
1:30 - What is {title}
3:45 - Key Benefits
6:20 - How to Implement
10:00 - Pro Tips
12:30 - Common Mistakes
15:00 - Conclusion

🔗 Resources Mentioned:
👉 Free Marketing Tools: https://growaimark.com/dashboard
👉 SEO Analyzer: https://growaimark.com/dashboard
👉 Keyword Research Tool: https://growaimark.com/dashboard

👍 Like, Subscribe & Share for more marketing tips!

🔔 Turn on notifications so you never miss an update!

#marketing #{title.lower().replace(' ', '')} #seo #digitalmarketing #businesstips #2024trends"""

        return jsonify({
            'success': True,
            'optimized_titles': optimized_titles,
            'optimized_description': optimized_desc,
            'tags': tags,
            'message': '🎬 YouTube SEO Optimized Successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CONTENT CALENDAR ====================
@app.route('/api/calendar/generate', methods=['POST'])
def generate_calendar():
    try:
        data = request.json
        niche = data.get('niche', 'marketing')

        content_ideas = {
            'marketing': [
                "Share a case study of your best marketing campaign",
                "Post 5 marketing statistics with insights",
                "Behind the scenes of your daily work",
                "Client success story (with permission)",
                "Marketing tip of the day series",
                "Ask followers about their biggest challenge",
                "Recommended marketing tools and resources"
            ],
            'seo': [
                "SEO myth vs fact: Debunk common misconceptions",
                "How to find low-competition keywords",
                "Backlink building strategies that work",
                "Local SEO tips for small businesses",
                "Technical SEO checklist for beginners",
                "SEO tools comparison and review",
                "Core Web Vitals optimization guide"
            ],
            'social': [
                "Engagement boosting strategies",
                "Content calendar template download",
                "Best times to post on each platform",
                "Hashtag strategy for more reach",
                "Video content ideas that convert",
                "Instagram Reels tips and tricks",
                "User-generated content campaigns"
            ]
        }

        ideas = content_ideas.get(niche, content_ideas['marketing'])
        platforms = ['Instagram', 'LinkedIn', 'Twitter', 'Facebook', 'TikTok']
        times = ['9 AM', '12 PM', '3 PM', '6 PM', '8 PM']

        calendar = []
        for i in range(7):
            calendar.append({
                'day': i + 1,
                'date': f"Day {i + 1}",
                'idea': ideas[i % len(ideas)],
                'platform': platforms[i % len(platforms)],
                'best_time': times[i % len(times)]
            })

        return jsonify({
            'success': True,
            'niche': niche,
            'calendar': calendar,
            'message': '📅 7-Day Content Calendar Generated!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== COMPETITOR ANALYSIS ====================
@app.route('/api/competitor/analyze', methods=['POST'])
def analyze_competitor():
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        return jsonify({
            'success': True,
            'url': url,
            'metrics': {
                'domain_authority': random.randint(25, 85),
                'monthly_traffic': random.randint(5000, 500000),
                'top_keywords': [
                    'digital marketing services',
                    'SEO agency',
                    'social media management',
                    'PPC campaigns',
                    'content marketing',
                    'email marketing tools'
                ],
                'backlinks': random.randint(500, 8000),
                'social_followers': random.randint(1000, 150000),
                'pages_indexed': random.randint(50, 5000)
            },
            'strengths': [
                "Strong domain authority",
                "Good social media presence",
                "Regular content publishing schedule",
                "Quality backlink profile"
            ],
            'weaknesses': [
                "Mobile optimization needs improvement",
                "Page speed could be faster",
                "Limited backlink diversity"
            ],
            'opportunities': [
                "Target long-tail keywords",
                "Improve mobile experience",
                "Create more video content",
                "Build relationships with industry influencers"
            ],
            'message': '🔍 Competitor Analysis Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== HASHTAG GENERATOR ====================
@app.route('/api/hashtags/generate', methods=['POST'])
def generate_hashtags():
    try:
        data = request.json
        topic = data.get('topic', '')

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        hashtags = [
            f"#{topic.replace(' ', '')}",
            f"#{topic.replace(' ', '')}Tips",
            f"#{topic.replace(' ', '')}Strategy",
            f"#{topic.replace(' ', '')}2024",
            "#DigitalMarketing",
            "#MarketingTips",
            "#BusinessGrowth",
            "#SEO",
            "#SocialMediaMarketing",
            "#ContentMarketing",
            "#MarketingStrategy",
            "#SmallBusiness",
            "#GrowthHacking",
            "#MarketingTools",
            "#AIMarketing",
            "#ViralMarketing",
            "#BrandBuilding",
            "#LeadGeneration",
            "#OnlineBusiness",
            "#MarketingExpert"
        ]

        return jsonify({
            'success': True,
            'topic': topic,
            'hashtags': hashtags[:20],
            'popular_hashtags': hashtags[:5],
            'niche_hashtags': hashtags[5:10],
            'message': '#️⃣ Hashtags Generated Successfully!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== KEYWORD RESEARCH ====================
@app.route('/api/keywords/suggest', methods=['POST'])
def suggest_keywords():
    try:
        data = request.json
        keyword = data.get('keyword', '')

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        keywords = [
            {'keyword': f'{keyword} services', 'volume': random.randint(500, 5000), 'competition': 'Medium',
             'cpc': round(random.uniform(1, 5), 2)},
            {'keyword': f'best {keyword}', 'volume': random.randint(800, 8000), 'competition': 'High',
             'cpc': round(random.uniform(2, 7), 2)},
            {'keyword': f'{keyword} agency', 'volume': random.randint(400, 4000), 'competition': 'Medium',
             'cpc': round(random.uniform(1.5, 4), 2)},
            {'keyword': f'{keyword} tools', 'volume': random.randint(600, 6000), 'competition': 'Low',
             'cpc': round(random.uniform(0.8, 3), 2)},
            {'keyword': f'affordable {keyword}', 'volume': random.randint(300, 3000), 'competition': 'Low',
             'cpc': round(random.uniform(0.5, 2.5), 2)},
            {'keyword': f'{keyword} expert', 'volume': random.randint(200, 2000), 'competition': 'Medium',
             'cpc': round(random.uniform(1.2, 3.5), 2)},
            {'keyword': f'{keyword} consultant', 'volume': random.randint(150, 1500), 'competition': 'Low',
             'cpc': round(random.uniform(1, 3), 2)},
            {'keyword': f'professional {keyword}', 'volume': random.randint(250, 2500), 'competition': 'Medium',
             'cpc': round(random.uniform(1.3, 3.8), 2)}
        ]

        return jsonify({
            'success': True,
            'keyword': keyword,
            'keywords': keywords,
            'message': '🔍 Keyword Research Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BACKLINK CHECKER ====================
@app.route('/api/backlink/analyze', methods=['POST'])
def analyze_backlinks():
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        return jsonify({
            'success': True,
            'url': url,
            'total_backlinks': random.randint(500, 10000),
            'referring_domains': random.randint(100, 1500),
            'dofollow_links': random.randint(300, 6000),
            'nofollow_links': random.randint(100, 3000),
            'top_backlinks': [
                {'domain': 'example1.com', 'authority': random.randint(40, 85), 'anchor_text': 'click here'},
                {'domain': 'example2.com', 'authority': random.randint(35, 75), 'anchor_text': 'learn more'},
                {'domain': 'example3.com', 'authority': random.randint(50, 90), 'anchor_text': 'check this'}
            ],
            'message': '🔗 Backlink Analysis Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== RANK TRACKER ====================
@app.route('/api/rank/track', methods=['POST'])
def track_rank():
    try:
        data = request.json
        keyword = data.get('keyword', '')

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        positions = [random.randint(5, 50) for _ in range(4)]

        return jsonify({
            'success': True,
            'keyword': keyword,
            'rankings': [
                {'date': 'Week 1', 'position': positions[0]},
                {'date': 'Week 2', 'position': positions[1]},
                {'date': 'Week 3', 'position': positions[2]},
                {'date': 'Week 4', 'position': positions[3]}
            ],
            'trend': 'improving' if positions[3] < positions[0] else 'declining',
            'current_position': positions[3],
            'improvement': positions[0] - positions[3],
            'message': '📈 Rank Tracking Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== INTERNATIONAL SEO ====================
@app.route('/api/international/seo', methods=['POST'])
def international_seo():
    try:
        data = request.json
        url = data.get('url', '')
        country = data.get('country', 'us')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        country_names = {
            'us': 'USA', 'uk': 'United Kingdom', 'de': 'Germany',
            'fr': 'France', 'it': 'Italy', 'es': 'Spain', 'nl': 'Netherlands'
        }

        return jsonify({
            'success': True,
            'url': url,
            'country': country_names.get(country, 'Global'),
            'score': random.randint(65, 98),
            'global_rank': random.randint(10000, 5000000),
            'country_rank': random.randint(500, 100000),
            'organic_traffic': {
                'us': random.randint(5000, 100000),
                'uk': random.randint(2000, 50000),
                'eu': random.randint(10000, 200000)
            },
            'recommendations': [
                "Create country-specific landing pages",
                "Use hreflang tags for multilingual SEO",
                "Build backlinks from local domains",
                "Optimize for local search engines"
            ],
            'message': f'🌍 International SEO Analysis for {country_names.get(country, "Global")} Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CURRENCY CONVERTER ====================
@app.route('/api/currency/convert', methods=['POST'])
def currency_convert():
    try:
        data = request.json
        amount = data.get('amount', 100)
        from_curr = data.get('from', 'USD')
        to_curr = data.get('to', 'EUR')

        rates = {
            'USD': 1, 'EUR': 0.92, 'GBP': 0.79, 'PKR': 278, 'CAD': 1.35, 'AUD': 1.52, 'INR': 83.5
        }

        converted = amount * rates.get(to_curr, 1) / rates.get(from_curr, 1)

        return jsonify({
            'success': True,
            'amount': amount,
            'from': from_curr,
            'to': to_curr,
            'converted': round(converted, 2),
            'rate': round(rates.get(to_curr, 1) / rates.get(from_curr, 1), 4),
            'message': f'💱 Converted {amount} {from_curr} to {round(converted, 2)} {to_curr}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== MULTI-LANGUAGE CONTENT ====================
@app.route('/api/multilanguage/content', methods=['POST'])
def multilanguage_content():
    try:
        data = request.json
        topic = data.get('topic', '')
        language = data.get('language', 'en')

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        languages = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French',
            'de': 'German', 'it': 'Italian', 'nl': 'Dutch'
        }

        templates = {
            'en': f"📝 **Blog Post: {topic.title()}**\n\nIntroduction to {topic.title()}... This is your complete guide.",
            'es': f"📝 **Artículo: {topic.title()}**\n\nIntroducción a {topic.title()}... Esta es tu guía completa.",
            'fr': f"📝 **Article: {topic.title()}**\n\nIntroduction à {topic.title()}... Ceci est votre guide complet.",
            'de': f"📝 **Blogbeitrag: {topic.title()}**\n\nEinführung in {topic.title()}... Dies ist Ihre vollständige Anleitung.",
            'it': f"📝 **Articolo: {topic.title()}**\n\nIntroduzione a {topic.title()}... Questa è la tua guida completa.",
            'nl': f"📝 **Blogpost: {topic.title()}**\n\nInleiding tot {topic.title()}... Dit is je complete gids."
        }

        return jsonify({
            'success': True,
            'topic': topic,
            'language': languages.get(language, 'English'),
            'content': templates.get(language, templates['en']),
            'message': f'🌍 Content generated in {languages.get(language, "English")}!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== MARKET INSIGHTS ====================
@app.route('/api/market/insights', methods=['POST'])
def market_insights():
    try:
        data = request.json
        industry = data.get('industry', 'marketing')
        market = data.get('market', 'us')

        insights = {
            'us': {
                'market_size': '$450 Billion',
                'growth_rate': '12.5%',
                'top_trends': ['AI Marketing', 'Voice Search', 'Video Content', 'Personalization'],
                'consumer_behavior': 'High digital adoption, prefers mobile-first experiences'
            },
            'uk': {
                'market_size': '$120 Billion',
                'growth_rate': '10.2%',
                'top_trends': ['Sustainability', 'Social Commerce', 'Influencer Marketing'],
                'consumer_behavior': 'Privacy-conscious, values transparency'
            },
            'eu': {
                'market_size': '$380 Billion',
                'growth_rate': '11.8%',
                'top_trends': ['GDPR Compliance', 'Localization', 'Omnichannel Marketing'],
                'consumer_behavior': 'Multi-lingual, values data protection'
            }
        }

        data = insights.get(market, insights['us'])

        return jsonify({
            'success': True,
            'market': market.upper(),
            'industry': industry,
            'market_size': data['market_size'],
            'growth_rate': data['growth_rate'],
            'top_trends': data['top_trends'],
            'consumer_behavior': data['consumer_behavior'],
            'message': f'📊 {market.upper()} Market Insights for {industry}!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== TRANSLATOR API ROUTES ====================
@app.route('/api/translate/video', methods=['POST'])
def translate_video():
    """API endpoint for video translation"""
    if translator is None:
        return jsonify({'success': False, 'error': 'Translator not available'}), 503

    try:
        data = request.json
        url = data.get('url', '')
        target_lang = data.get('language', 'urdu')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        result = translator.process_video(url, target_lang)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/text', methods=['POST'])
def translate_text_api():
    """API endpoint for direct text translation"""
    if translator is None:
        return jsonify({'success': False, 'error': 'Translator not available'}), 503

    try:
        data = request.json
        text = data.get('text', '')
        target_lang = data.get('language', 'urdu')

        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400

        result = translator.translate_direct_text(text, target_lang)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/languages')
def get_languages():
    """Get supported languages"""
    languages = {
        'urdu': '🇵🇰 Urdu (Easy to understand)',
        'english': '🇬🇧 English',
        'hindi': '🇮🇳 Hindi',
        'arabic': '🇸🇦 Arabic',
        'french': '🇫🇷 French',
        'german': '🇩🇪 German',
        'spanish': '🇪🇸 Spanish',
        'turkish': '🇹🇷 Turkish',
        'bangla': '🇧🇩 Bangla',
        'pashto': '🇦🇫 Pashto'
    }
    return jsonify(languages)


# ==================== BLOG API ====================
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
        'image_url': p.get('image_url', ''),
        'excerpt': p['excerpt']
    } for p in posts])


@app.route('/api/blog/post/<slug>')
def get_blog_post(slug):
    posts = load_blog_posts()
    for post in posts:
        if post['slug'] == slug:
            return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


@app.route('/api/blog/post/<int:post_id>')
def get_blog_post_by_id(post_id):
    posts = load_blog_posts()
    for post in posts:
        if post['id'] == post_id:
            return jsonify(post)
    return jsonify({'error': 'Post not found'}), 404


@app.route('/api/blog/post/save', methods=['POST'])
def save_blog_post():
    data = request.json
    posts = load_blog_posts()

    if data.get('id'):
        for i, post in enumerate(posts):
            if post['id'] == data['id']:
                data['comments'] = post.get('comments', [])
                posts[i] = data
                break
    else:
        new_id = max([p['id'] for p in posts], default=0) + 1
        data['id'] = new_id
        data['comments'] = []
        posts.append(data)

    save_blog_posts(posts)
    return jsonify({'success': True, 'id': data['id']})


@app.route('/api/blog/post/<int:post_id>/delete', methods=['DELETE'])
def delete_blog_post(post_id):
    posts = load_blog_posts()
    posts = [p for p in posts if p['id'] != post_id]
    save_blog_posts(posts)
    return jsonify({'success': True})


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


@app.route('/api/blog/upload-image', methods=['POST'])
def upload_blog_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{int(datetime.now().timestamp())}_{name}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        image_url = f"/static/uploads/{filename}"
        return jsonify({'success': True, 'url': image_url})

    return jsonify({'error': 'Invalid file type'}), 400


# ==================== PRICING API ====================
@app.route('/api/pricing')
def get_pricing():
    return jsonify({
        'free': {
            'name': 'Free Forever',
            'price': 0,
            'daily_limit': 'Unlimited',
            'tools': ['All 10+ Tools'],
            'features': ['Unlimited Usage', 'No Credit Card Required', 'Full Access']
        }
    })


# ==================== USAGE CHECK ====================
@app.route('/api/usage/check')
def check_usage():
    return jsonify({
        'success': True,
        'plan': 'free',
        'limit': 'Unlimited',
        'message': 'All tools are completely free!'
    })


# ==================== RUN APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG') == '1')