import os
import json
import redis
import psycopg2
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Fallback mechanism agar Environment Variables set na hon
REDIS_URL = os.getenv('REDIS_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '')
        cgpa = request.form.get('cgpa', '')
        
        # 1. Cache to Redis (agar URL configured ho)
        if REDIS_URL:
            try:
                r = redis.Redis.from_url(REDIS_URL)
                data = json.dumps({'name': name, 'cgpa': cgpa})
                r.set(f"student:{name}", data)
            except Exception as e:
                pass
        
        # 2. Write to DB (agar DATABASE_URL configured ho)
        if DATABASE_URL:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS students (id SERIAL PRIMARY KEY, name VARCHAR(255), cgpa VARCHAR(10))")
                cursor.execute("INSERT INTO students (name, cgpa) VALUES (%s, %s)", (name, cgpa))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                pass
        
        return "<h3>Submitted successfully! Go to /results</h3>"
        
    return '<form method="POST">Name: <input name="name"><br>CGPA: <input name="cgpa"><br><input type="submit"></form>'

@app.route('/results')
def results():
    students = []
    if REDIS_URL:
        try:
            r = redis.Redis.from_url(REDIS_URL)
            students = [json.loads(r.get(k)) for k in r.keys("student:*") if r.get(k)]
        except Exception as e:
            pass
    return render_template_string('<h2>Results</h2><ul>{% for s in students %}<li>{{s.name}} - {{s.cgpa}}</li>{% endfor %}</ul>', students=students)