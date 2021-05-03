from chalice import Chalice
from chalicelib.elevate.api import lambda_handler

app = Chalice(app_name='elevate-api')


@app.route('/alive')
def index():
    return {'alive': True}


@app.route('/incidents')
def index():
    return lambda_handler()
