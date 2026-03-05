from flask import Flask, render_template

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return "<h1>About Us</h1>"

@app.route('/contact')
def contact():
    return "<h1>Contact Us</h1>"

if __name__ == '__main__':
    app.run(debug=True)