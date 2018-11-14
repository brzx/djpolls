from mysite.wsgi import application
from waitress import serve

serve(application, host='0.0.0.0', port=5000)