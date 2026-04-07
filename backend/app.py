from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.auth import auth_bp
from routes.analisis import analisis_bp
from routes.resultados import resultados_bp
from routes.perfil import perfil_bp
from routes.antecedentes import antecedentes_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

app.register_blueprint(auth_bp,          url_prefix='/api')
app.register_blueprint(analisis_bp,      url_prefix='/api')
app.register_blueprint(resultados_bp,    url_prefix='/api')
app.register_blueprint(perfil_bp,        url_prefix='/api')
app.register_blueprint(antecedentes_bp,  url_prefix='/api')

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/cuestionario.html')
def cuestionario():
    return send_from_directory('../frontend', 'cuestionario.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)