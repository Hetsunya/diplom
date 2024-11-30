# predict.py

import tensorflow as tf
import numpy as np
from config import label_mapping, MODEL, IMG_SIZE
from tensorflow.keras.preprocessing import image

# Загрузите вашу модель
model = tf.keras.models.load_model(MODEL)

# Функция для предсказания
def predict_image(img_path):
    img = image.load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))  # Пример для MobileNetV2
    img_array = image.img_to_array(img)  # Преобразуем изображение в массив
    img_array = np.expand_dims(img_array, axis=0)  # Добавляем размерность для батча

    # Нормализуем изображение (если необходимо для модели)
    img_array = img_array / 255.0  # Если модель обучалась на таких данных

    # Получаем предсказание
    predictions = model.predict(img_array)

    # Находим метку с максимальной вероятностью
    predicted_idx = np.argmax(predictions)  # Получаем индекс с максимальной вероятностью
    predicted_label = [label for label, idx in label_mapping.items() if idx == predicted_idx][0]  # Находим метку по индексу

    return predicted_label, predictions[0][predicted_idx]  # Возвращаем метку и вероятность

# Пример использования
img_path = 'data/sad/image0030370.jpg'
predicted_label, confidence = predict_image(img_path)

print(f"Предсказанная метка: {predicted_label}, вероятность: {confidence}")
