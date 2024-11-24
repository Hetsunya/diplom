import os
import pandas as pd
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.optimizers import Adam

# Путь к данным
image_dir = 'data/'

# Генератор для подготовки данных
train_datagen = ImageDataGenerator(rescale=1./255)  # Нормализация изображений
test_datagen = ImageDataGenerator(rescale=1./255)

# Подготовим генератор для тренировки
train_generator = train_datagen.flow_from_directory(
    image_dir,  # Папка с изображениями
    target_size=(224, 224),  # Размер изображений для модели
    batch_size=32,  # Размер батча
    class_mode='categorical'  # Используем one-hot кодирование для меток
)

# Подготовим генератор для тестирования
test_generator = test_datagen.flow_from_directory(
    image_dir,  # Папка с изображениями
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

from tensorflow.keras.applications import ResNet50

# Загружаем предобученную модель ResNet50
base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Замораживаем слои базы модели
base_model.trainable = False

# Строим модель
model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dropout(0.5),
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(8, activation='softmax')  # 8 эмоций
])

# Компилируем модель
model.compile(optimizer=Adam(learning_rate=0.0001), loss='categorical_crossentropy', metrics=['accuracy'])

# Обзор модели
model.summary()


# Обучаем модель
history = model.fit(
    train_generator,
    epochs=10,  # Количество эпох
    validation_data=test_generator
)

# Сохраняем модель
model.save('emotion_recognition_model.h5')
model.save('emotion_recognition_model.keras')

# Оценка на тестовых данных
test_loss, test_acc = model.evaluate(test_generator)
print(f"Test accuracy: {test_acc}")


