import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from config import IMG_SIZE, BATCH_SIZE, EPOCHS, LEARNING_RATE, DATASET_PATH

from tensorflow.keras.applications import EfficientNetB0

from tensorflow.keras.applications import ResNet50

def create_model_ResNet50(img_size, num_classes):
    base_model = ResNet50(
        input_shape=(img_size, img_size, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False  # Замораживаем веса базовой модели

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    return model

def create_model_EfficientNetB0(img_size, num_classes):
    base_model = EfficientNetB0(
        input_shape=(img_size, img_size, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False  # Замораживаем веса базовой модели

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    return model

# Параметры
SEED = 123  # Для воспроизводимости

# Аугментация данных
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,  # Нормализация
    rotation_range=30,  # Вращение
    width_shift_range=0.2,  # Сдвиг по ширине
    height_shift_range=0.2,  # Сдвиг по высоте
    shear_range=0.2,  # Сдвиг по углу
    zoom_range=0.2,  # Зум
    horizontal_flip=True,  # Горизонтальное отражение
    fill_mode="nearest",  # Заполнение пустого пространства
    brightness_range=[0.8, 1.2],  # Изменение яркости
    validation_split=0.2  # Разделение на обучение и валидацию
)

# Генераторы данных
train_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="sparse",  # Метки в виде целых чисел
    subset="training",
    seed=SEED
)

val_datagen = ImageDataGenerator(
    rescale=1.0/255,  # Нормализация
    validation_split=0.2
)

val_generator = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="sparse",
    subset="validation",
    seed=SEED
)

# Создание модели
def create_model(img_size, num_classes):
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(img_size, img_size, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False  # Замораживаем веса базовой модели

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model

# Инициализация модели
model = create_model_ResNet50(IMG_SIZE, num_classes=len(train_generator.class_indices))

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard, ReduceLROnPlateau, CSVLogger, \
    BackupAndRestore

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
        min_lr=1e-9
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
# Callbacks
callbacks = get_callbacks()

# Обучение модели
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    callbacks=callbacks
)

# Сохранение итоговой модели
model.save("model/final_model.keras")
print("Модель сохранена!")
