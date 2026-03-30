from flask import Flask, send_from_directory
import os

# Pehle app create karo
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Phir routes define karo
@app.route('/')
def home():
    return "<h1>GrowAIMark</h1><p>Flask App Running Successfully!</p>"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images', 'favicon.ico',
                              mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)