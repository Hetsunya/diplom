import cv2
from fer import FER

# Инициализация детектора эмоций
detector = FER()

# Инициализация камеры
cap = cv2.VideoCapture(0)  # 0 - камера по умолчанию

# Устанавливаем шрифт для текста
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    # Чтение кадра из камеры
    ret, frame = cap.read()

    # Если кадр считан успешно, делаем предсказание
    if ret:
        # Получаем список всех обнаруженных лиц и эмоций
        results = detector.detect_emotions(frame)

        for face_info in results:
            # Координаты лица (x, y, w, h)
            x, y, w, h = face_info["box"]
            emotions = face_info["emotions"]

            # Определяем эмоцию с максимальной вероятностью
            top_emotion, score = max(emotions.items(), key=lambda item: item[1])

            # Отрисовка прямоугольника вокруг лица
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Отображение эмоции и её вероятности
            label_text = f"{top_emotion}: {score*100:.2f}%"
            cv2.putText(frame, label_text, (x, y - 10), font, 0.6, (255, 0, 0), 2, cv2.LINE_AA)

        # Если лица не обнаружены, выводим сообщение
        if not results:
            cv2.putText(frame, "No face detected", (10, 30), font, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Показываем кадр
        cv2.imshow("Predicted Emotion", frame)

    # Прерывание, если нажата клавиша 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
