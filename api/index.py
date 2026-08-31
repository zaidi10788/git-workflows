import os, json
import redis
import psycopg2 # Using Postgres (Vercel's default SQL) instead of MySQL
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Connect to Cloud Redis (Vercel KV or Upstash)
r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

def get_db_connection():
    # Connect to Cloud SQL (Vercel Postgres)
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        cgpa = request.form['cgpa']
        
        # 1. Cache to Redis (App 1 logic)
        data = json.dumps({'name': name, 'cgpa': cgpa})
        r.set(f"student:{name}", data)
        
        # 2. Write directly to DB (Replaces Background Worker)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS students (id SERIAL PRIMARY KEY, name VARCHAR(255), cgpa VARCHAR(10))")
        cursor.execute("INSERT INTO students (name, cgpa) VALUES (%s, %s)", (name, cgpa))
        conn.commit()
        cursor.close()
        conn.close()
        
        return "<h3>Submitted successfully! Go to /results</h3>"
        
    return '<form method="POST">Name: <input name="name"><br>CGPA: <input name="cgpa"><br><input type="submit"></form>'

@app.route('/results')
def results():
    # App 2 logic
    students = [json.loads(r.get(k)) for k in r.keys("student:*") if r.get(k)]
    return render_template_string('<h2>Results</h2><ul>{% for s in students %}<li>{{s.name}} - {{s.cgpa}}</li>{% endfor %}</ul>', students=students)

# Vercel requires the app instance to be available as a variable