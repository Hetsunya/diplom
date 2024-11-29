import os
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
from config import IMG_SIZE, EPOCHS, BATCH_SIZE, LEARNING_RATE
from data_loader import load_datasets

# Загружаем данные
train_ds, test_ds = load_datasets(True, True)


# Определяем модель
def create_model():
    model = models.Sequential([
        layers.InputLayer(input_shape=(IMG_SIZE, IMG_SIZE, 3)),  # Входной слой для изображений размером 224x224
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(10, activation='softmax')  # Количество классов - 10
    ])

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model


# Колбеки для обучения
def get_callbacks():
    # Папка для хранения логов и модели
    checkpoint_dir = os.path.join('model', 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Колбек для сохранения лучшей модели по валидационной точности
    checkpoint_callback = ModelCheckpoint(
        os.path.join(checkpoint_dir, 'best_model.keras'),
        save_best_only=True,
        monitor='val_accuracy',
        mode='max',
        verbose=1
    )

    # Колбек для ранней остановки, если валидационная точность не улучшается
    early_stopping_callback = EarlyStopping(
        monitor='val_accuracy',
        patience=3,  # Останавливаем обучение после 3 эпох без улучшений
        restore_best_weights=True,
        verbose=1
    )

    # Колбек для TensorBoard
    tensorboard_callback = TensorBoard(
        log_dir=os.path.join('model', 'logs'),
        histogram_freq=1,
        write_graph=True,
        write_images=True
    )

    return [checkpoint_callback, early_stopping_callback, tensorboard_callback]


# Обучение модели
def train_model():
    model = create_model()

    # Получаем колбеки
    callbacks = get_callbacks()

    # Обучаем модель
    history = model.fit(train_ds,
                        epochs=EPOCHS,
                        validation_data=test_ds,
                        verbose=1,
                        callbacks=callbacks)

    # Сохраняем модель в конце обучения
    model.save(os.path.join('model', 'final_model.keras'))
    print("Модель сохранена!")

    return history


if __name__ == "__main__":
    # Начинаем обучение
    history = train_model()

    # Выводим результаты обучения
    print("История обучения:", history.history)
    print(
        f"Лучший результат: {max(history.history['val_accuracy']):.4f} на эпохе {history.history['val_accuracy'].index(max(history.history['val_accuracy'])) + 1}")
