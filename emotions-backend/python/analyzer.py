from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    # Получаем данные от Go (например, путь к видео)
    data = request.json
    video_path = data.get('video', '')

    # Заглушка: возвращаем фиксированные эмоции
    emotions = {
        'Радость': 0.85,
        'Грусть': 0.10,
        'Гнев': 0.03,
        'Страх': 0.01,
        'Удивление': 0.01,
        'Отвращение': 0.0,
        'Нейтральное': 0.0
    }

    return jsonify(emotions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)