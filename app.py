from flask import Flask, render_template
from flask import jsonify  
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Connexion à la base de données
    conn = sqlite3.connect('people_counting.db')
    c = conn.cursor()

    # Total des personnes uniques (track_id + session_id combinés)
    c.execute('SELECT COUNT(DISTINCT track_id || session_id) FROM counts')
    total_people = c.fetchone()[0]

    # Activité récente (les 10 dernières détections)
    c.execute('SELECT timestamp, track_id, session_id FROM counts ORDER BY timestamp DESC LIMIT 10')
    recent_activity = c.fetchall()

    # Données horaires : nombre de personnes uniques par heure
    c.execute('''
        SELECT strftime("%H", timestamp) as hour,
               COUNT(DISTINCT track_id || session_id)
        FROM counts
        GROUP BY hour
        ORDER BY hour
    ''')
    hourly_data = c.fetchall()

    conn.close()

    # Rendu du template avec les données et l'objet datetime
    return render_template(
        'dashboard.html',
        total_people=total_people,
        recent_activity=recent_activity,
        hourly_data=hourly_data,
        datetime=datetime  # important pour résoudre l'erreur que tu avais
    )
    # Ajoutez cette nouvelle route avant le if __name__ == '__main__':
@app.route('/api/people_count')
def api_people_count():
    conn = sqlite3.connect('people_counting.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT track_id || session_id) FROM counts')
    total_people = c.fetchone()[0]
    
    # Récupérez aussi les 10 dernières activités pour la mise à jour
    c.execute('SELECT timestamp, track_id, session_id FROM counts ORDER BY timestamp DESC LIMIT 10')
    recent_activity = c.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_people': total_people,
        'recent_activity': recent_activity,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })


if __name__ == '__main__':
    app.run(debug=True)
