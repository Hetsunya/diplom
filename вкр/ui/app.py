from flask import Flask, render_template, redirect, url_for, request, jsonify
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# Тестовые данные сессий
sessions = [
    {
        'id': 1,
        'type': 'Собеседование',
        'start_time': (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M"),
        'status': 'planned',
        'participants': ['Кандидат А', 'HR-специалист'],
        'config_id': 1  # Привязка конфига
    },
    {
        'id': 2,
        'type': 'Совещание',
        'start_time': datetime.now().strftime("%Y-%m-%dT%H:%M"),
        'status': 'ready',
        'participants': ['Иванов', 'Петров', 'Сидорова'],
        'config_id': 2
    },
    {
        'id': 3,
        'type': 'Совещание',
        'start_time': (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
        'end_time': (datetime.now() - timedelta(hours=1, minutes=30)).strftime("%d.%m.%Y %H:%M"),
        'status': 'completed',
        'participants': ['Петров', 'Сидорова', 'Козлов'],
        'config_id': 2,
        'emotions': {
            'timeline': ['0 мин', '5 мин', '10 мин', '15 мин', '20 мин', '25 мин', '30 мин'],
            'participants': {
                'Петров': {
                    'радость': [40, 45, 50, 48, 45, 42, 40],
                    'стресс': [30, 35, 40, 55, 60, 50, 45],
                    'нейтрально': [30, 20, 10, 5, 5, 8, 15],
                    'вовлеченность': [70, 75, 80, 75, 70, 65, 60]
                },
                'Сидорова': {
                    'радость': [20, 25, 30, 25, 20, 15, 10],
                    'стресс': [60, 65, 70, 75, 80, 70, 60],
                    'нейтрально': [20, 10, 0, 0, 0, 15, 30],
                    'вовлеченность': [40, 35, 30, 25, 20, 30, 40]
                }
            },
            'risks': [
                "Высокий стресс у Сидоровой в период 15-20 мин",
                "Низкая вовлеченность Сидоровой в первые 10 минут"
            ]
        }
    }
]

# Тестовые конфигурации
configs = [
    {
        'id': 1,
        'name': 'Стандартное собеседование',
        'description': 'Акцент на стрессоустойчивость и искренность',
        'video_model': 'vgg-face',
        'audio_model': 'lstm-ravdess',
        'emotions': ['стресс', 'радость', 'обман'],
        'min_confidence': 85,
        'interval_sec': 2,
        'anonymize': True,
        'retention_days': 1
    },
    {
        'id': 2,
        'name': 'Командное совещание',
        'description': 'Анализ групповой динамики',
        'video_model': 'mobile-net',
        'audio_model': 'lstm-ravdess',
        'emotions': ['вовлеченность', 'раздражение', 'согласие'],
        'min_confidence': 75,
        'interval_sec': 5,
        'anonymize': True,
        'retention_days': 7
    }
]

def generate_emotion_data(participants):
    """Генерация тестовых данных эмоций"""
    return {
        'timeline': [f"{i} мин" for i in range(0, 31, 5)],
        'participants': {
            p: {
                'стресс': [random.randint(20, 80) for _ in range(7)],
                'вовлеченность': [random.randint(30, 90) for _ in range(7)],
                'радость': [random.randint(10, 70) for _ in range(7)],
                'нейтрально': [random.randint(5, 50) for _ in range(7)]
            } for p in participants
        },
        'risks': [
            f"Повышенный стресс у {random.choice(participants)} в период 10-15 мин",
            f"Низкая вовлеченность у {random.choice(participants)} в начале сессии"
        ]
    }

# === ОСНОВНЫЕ СТРАНИЦЫ ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sessions')
def sessions_list():
    now = datetime.now()
    for session in sessions:
        session_time = datetime.strptime(session['start_time'], "%Y-%m-%dT%H:%M")
        if session['status'] == 'planned' and session_time <= now:
            session['status'] = 'ready'
    return render_template('sessions.html', sessions=sessions)

@app.route('/configs')
def configs_page():
    """Страница конструктора конфигов"""
    return render_template('configs.html', configs=configs)

@app.route('/session/<int:session_id>/start', methods=['POST'])
def start_session(session_id):
    for session in sessions:
        if session['id'] == session_id and session['status'] in ['ready', 'active']:
            session['status'] = 'active'
            return render_template('video_meet.html', session=session)
    return "Сессия недоступна для запуска", 400

@app.route('/session/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    for session in sessions:
        if session['id'] == session_id and session['status'] == 'active':
            session['status'] = 'completed'
            session['end_time'] = datetime.now().strftime("%d.%m.%Y %H:%M")
            session['emotions'] = generate_emotion_data(session['participants'])
            return redirect(url_for('report', session_id=session_id))
    return "Невозможно завершить сессию", 400

@app.route('/session/<int:session_id>/report')
def report(session_id):
    session = next((s for s in sessions if s['id'] == session_id), None)
    if not session or session.get('status') != 'completed':
        return "Отчет не готов", 404
    return render_template('report.html', session=session)

@app.route('/dashboard')
def dashboard():
    completed_sessions = [s for s in sessions if s.get('status') == 'completed']
    
    chart_data = {
        'labels': [f"Сессия {s['id']}" for s in completed_sessions],
        'stress': [random.randint(40, 85) for _ in completed_sessions],
        'engagement': [random.randint(50, 95) for _ in completed_sessions]
    }
    
    return render_template('dashboard.html', 
                         sessions=completed_sessions, 
                         chart_data=chart_data)

# === API ДЛЯ КОНФИГОВ ===
@app.route('/api/configs')
def get_configs():
    """Получение списка конфигов"""
    return jsonify(configs)

@app.route('/api/config/<int:config_id>')
def get_config(config_id):
    """Получение деталей конфига"""
    config = next((c for c in configs if c['id'] == config_id), None)
    if not config:
        return jsonify({'error': 'Конфиг не найден'}), 404
    return jsonify(config)

@app.route('/api/session/<int:session_id>/set_config', methods=['POST'])
def set_session_config(session_id):
    """Привязка конфига к сессии"""
    config_id = request.json.get('config_id')
    
    session = next((s for s in sessions if s['id'] == session_id), None)
    if not session:
        return jsonify({'error': 'Сессия не найдена'}), 404
    
    session['config_id'] = config_id
    return jsonify({'success': True, 'session_id': session_id, 'config_id': config_id})

# === СТРАНИЦА СОЗДАНИЯ СЕССИИ С ВЫБОРОМ КОНФИГА ===
@app.route('/new_session', methods=['GET', 'POST'])
def new_session():
    if request.method == 'POST':
        session_type = request.form['type']
        config_id = int(request.form['config_id'])
        
        new_id = max(s['id'] for s in sessions) + 1 if sessions else 1
        new_session = {
            'id': new_id,
            'type': 'Собеседование' if session_type == 'interview' else 'Совещание',
            'start_time': datetime.now().strftime("%Y-%m-%dT%H:%M"),
            'status': 'ready',
            'participants': ['Новый участник 1', 'Новый участник 2'],
            'config_id': config_id
        }
        sessions.append(new_session)
        
        return redirect(url_for('sessions_list'))
    
    return render_template('new_session.html', configs=configs)

if __name__ == '__main__':
    app.run(debug=True)