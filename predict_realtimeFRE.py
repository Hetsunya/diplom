# predict_realtime_fer.py

import cv2
from fer import FER

# Инициализация детектора эмоций
detector = FER()

# Инициализация камеры
cap = cv2.VideoCapture(0)  # 0 - обычно камера по умолчанию

while True:
    # Чтение кадра из камеры
    ret, frame = cap.read()

    # Если кадр считан успешно, делаем предсказание
    if ret:
        # Детектируем эмоции на текущем кадре
        emotions, score = detector.top_emotion(frame)

        # Проверка на None (если эмоции не распознаны)
        if emotions and score is not None:
            # Отображаем предсказание на кадре
            font = cv2.FONT_HERSHEY_SIMPLEX
            label_text = f"{emotions}: {score*100:.2f}%"
            cv2.putText(frame, label_text, (10, 30), font, 1, (255, 0, 0), 2, cv2.LINE_AA)
        else:
            # Если эмоции не распознаны, показываем сообщение
            cv2.putText(frame, "No face detected", (10, 30), font, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Показываем кадр
        cv2.imshow("Predicted Emotion", frame)

    # Прерывание, если нажата клавиша 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
