import cv2
import tensorflow as tf
import numpy as np
from config import label_mapping, MODEL, IMG_SIZE, BEST_MODEL
from tensorflow.keras.preprocessing import image

# Загружаем модель
model = tf.keras.models.load_model(BEST_MODEL)

# Функция для предсказания метки
def predict_frame(frame):
    # Преобразуем изображение из формата OpenCV в формат, подходящий для модели
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV использует BGR, а модель ожидает RGB
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

    # Если кадр считан успешно, делаем предсказание
    if ret:
        # Получаем предсказание для текущего кадра
        predicted_label, confidence = predict_frame(frame)

        # Отображаем предсказание на кадре
        font = cv2.FONT_HERSHEY_SIMPLEX
        label_text = f"{predicted_label}: {confidence*100:.2f}%"
        cv2.putText(frame, label_text, (10, 30), font, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # Показываем кадр
        cv2.imshow("Predicted Emotion", frame)

    # Прерывание, если нажата клавиша 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
