from flask import Flask, render_template, redirect, url_for, session, request
from config import Config
from translations import TRANSLATIONS
from routes.auth_routes import auth_bp
from routes.customer_routes import customer_bp
from routes.admin_routes import admin_bp
from routes.technician_routes import technician_bp
from routes.owner_routes import owner_bp

app = Flask(__name__)
app.config.from_object(Config)

# Blueprints Register කිරීම
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(technician_bp)
app.register_blueprint(owner_bp)

# භාෂාව මාරු කරන Route එක (BuildError මඟහරවා ගැනීමට මෙය අත්‍යවශ්‍ය වේ)
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['en', 'si', 'ta']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('auth.login'))

# සියලුම Templates වෙත Language සහ Translation පහසුකම ලබාදීම
@app.context_processor
def inject_language():
    lang = session.get('lang', 'si')  # පෙර ነියමිත භාෂාව සිංහල ලෙස
    def t(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS['si']).get(key, key)
    return dict(t=t, current_lang=lang)

@app.route('/')
def home():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)