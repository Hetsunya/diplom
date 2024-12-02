import cv2
import tensorflow as tf
import numpy as np
from config import label_mapping, MODEL, IMG_SIZE
from tensorflow.keras.preprocessing import image

# Загружаем модель
model = tf.keras.models.load_model(MODEL)

# Инициализация детектора лиц (используется встроенный детектор OpenCV)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Функция для предсказания метки
def predict_frame(face_frame):
    # Преобразуем изображение из формата OpenCV в формат, подходящий для модели
    img = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)  # OpenCV использует BGR, а модель ожидает RGB
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))  # Приводим к размеру, который требуется модели
    img_array = image.img_to_array(img)  # Преобразуем в массив
    img_array = np.expand_dims(img_array, axis=0)  # Добавляем размерность для батча

    # Нормализуем изображение (если модель обучалась на таких данных)
    img_array = img_array / 255.0  # Это зависит от того, как обучалась модель

    # Получаем предсказание
    predictions = model.predict(img_array)

    # Находим метку с максимальной вероятностью
    predicted_idx = np.argmax(predictions)  # Получаем индекс с максимальной вероятностью
    predicted_label = [label for label, idx in label_mapping.items() if idx == predicted_idx][0]  # Находим метку по индексу

    return predicted_label, predictions[0][predicted_idx]  # Возвращаем метку и вероятность

# Инициализация камеры
cap = cv2.VideoCapture(0)  # 0 - обычно камера по умолчанию

while True:
    # Чтение кадра из камеры
    ret, frame = cap.read()

    # Если кадр считан успешно
    if ret:
        # Конвертируем кадр в серый для обнаружения лиц
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            # Извлекаем область лица
            face_frame = frame[y:y+h, x:x+w]

            # Получаем предсказание для области лица
            predicted_label, confidence = predict_frame(face_frame)

            # Отрисовываем прямоугольник вокруг лица
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # Отображаем предсказание на кадре
            font = cv2.FONT_HERSHEY_SIMPLEX
            label_text = f"{predicted_label}: {confidence*100:.2f}%"
            cv2.putText(frame, label_text, (x, y - 10), font, 0.6, (255, 0, 0), 2, cv2.LINE_AA)

        # Если лица не обнаружены, выводим сообщение
        if len(faces) == 0:
            cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Показываем кадр
        cv2.imshow("Predicted Emotion", frame)

    # Прерывание, если нажата клавиша 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
