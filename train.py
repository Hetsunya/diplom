import os
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from config import IMG_SIZE, EPOCHS, BATCH_SIZE, LEARNING_RATE, LABELS
from data_loader import load_datasets
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard, ReduceLROnPlateau, CSVLogger, \
    BackupAndRestore
# Загружаем данные
train_ds, test_ds = load_datasets(True, True, batch_size=200000)

# Определяем модель
def create_model():
    # Загружаем MobileNetV2 с предварительно обученными весами (imagenet)
    base_model = tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                                   include_top=False,
                                                   weights='imagenet')

    # Замораживаем веса базовой модели
    base_model.trainable = True

    # Размораживаем последние несколько слоев
    # for layer in base_model.layers[-20:]:
    #     layer.trainable = True

    # Создаем модель
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        # layers.Dense(1024, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        # layers.BatchNormalization(),
        # layers.Dropout(0.5),
        # layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        # layers.BatchNormalization(),
        # layers.Dropout(0.5),
        layers.Dense(LABELS, activation='softmax')
    ])

    # model.compile(optimizer=tf.keras.optimizers.RMSprop(learning_rate=LEARNING_RATE),
    #               loss='sparse_categorical_crossentropy',
    #               metrics=['accuracy'])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    return model


def get_callbacks():
    # Папка для хранения логов и модели
    checkpoint_dir = os.path.join('model', 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)

    # ModelCheckpoint для сохранения лучшей модели
    checkpoint_callback = ModelCheckpoint(
        os.path.join(checkpoint_dir, 'best_model.keras'),
        save_best_only=True,
        monitor='val_accuracy',
        mode='max',
        verbose=1
    )

    # EarlyStopping для остановки обучения, если модель не улучшается
    early_stopping_callback = EarlyStopping(
        monitor='val_loss',
        patience=3,
        restore_best_weights=True,
        verbose=1
    )

    # TensorBoard для логирования и визуализации данных
    tensorboard_callback = TensorBoard(
        log_dir=os.path.join('model', 'logs'),
        histogram_freq=1,
        write_graph=True,
        write_images=True
    )

    # ReduceLROnPlateau для уменьшения learning rate, если нет улучшений
    reduce_lr_callback = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.3,
        patience=2,
        verbose=1,
        min_lr=1e-19
    )

    # CSVLogger для записи истории обучения в CSV файл
    csv_logger = CSVLogger(os.path.join('model', 'training_log.csv'), append=True)

    # BackUpAndRestore для создания резервных копий модели в процессе обучения
    backup_restore_callback = BackupAndRestore(
        backup_dir=os.path.join('model', 'backup'),
        save_freq='epoch'
    )

    return [
        checkpoint_callback,
        early_stopping_callback,
        tensorboard_callback,
        reduce_lr_callback,
        csv_logger,
        backup_restore_callback,
    ]


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
