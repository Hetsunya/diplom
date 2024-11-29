import os
import numpy as np
import tensorflow as tf
from config import PROCESSED_DIR, BATCH_SIZE, IMG_SIZE
# Константы
AUTO = tf.data.AUTOTUNE  # Автоматическая настройка для параллельной загрузки данных


def load_npy_batches(data_type, batch_size=1000):
    """
    Загружает данные (train или test) из .npy файлов по частям.
    :param data_type: Тип данных ('train' или 'test').
    :param batch_size: Размер пакета для загрузки.
    :return: Кортеж (изображения, метки).
    """
    images = []
    labels = []
    batch_prefix = f"X_{data_type}_batch_"
    label_prefix = f"y_{data_type}_batch_"

    # Получаем все файлы для данного типа данных
    image_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.startswith(batch_prefix)])
    label_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.startswith(label_prefix)])

    for img_file, lbl_file in zip(image_files, label_files):
        img_path = os.path.join(PROCESSED_DIR, img_file)
        lbl_path = os.path.join(PROCESSED_DIR, lbl_file)
        img_batch = np.load(img_path)  # Загружаем изображения
        lbl_batch = np.load(lbl_path)  # Загружаем метки

        # Сохраняем в списки
        images.append(img_batch)
        labels.append(lbl_batch)

        # Если достигнут размер батча, возвращаем данные
        if len(images) >= batch_size:
            yield np.concatenate(images, axis=0), np.concatenate(labels, axis=0)
            images = []  # Сбрасываем список
            labels = []  # Сбрасываем список

    # Обработка оставшихся данных
    if len(images) > 0:
        yield np.concatenate(images, axis=0), np.concatenate(labels, axis=0)


def create_tf_dataset(images, labels, shuffle=True, augment=False):
    """
    Создает tf.data.Dataset для подачи в модель.

    :param images: Массив изображений.
    :param labels: Массив меток.
    :param shuffle: Если True, данные будут перемешаны.
    :param augment: Если True, применяются аугментации.
    :return: tf.data.Dataset.
    """
    dataset = tf.data.Dataset.from_tensor_slices((images, labels))

    if shuffle:
        dataset = dataset.shuffle(buffer_size=len(labels), reshuffle_each_iteration=True)

    if augment:
        def augment_image(image, label):
            image = tf.image.random_flip_left_right(image)
            image = tf.image.random_flip_up_down(image)
            return image, label

        dataset = dataset.map(augment_image, num_parallel_calls=AUTO)

    dataset = dataset.batch(BATCH_SIZE).prefetch(AUTO)
    return dataset


def load_datasets(shuffle=True, augment=False):
    """
    Загружает данные из обработанных файлов и создает tf.data.Dataset.

    :param shuffle: Если True, данные будут перемешаны.
    :param augment: Если True, применяются аугментации.
    :return: Кортеж (train_dataset, test_dataset).
    """
    print("Загрузка TRAIN данных...")
    train_generator = load_npy_batches("train", batch_size=100)

    print("Загрузка TEST данных...")
    test_generator = load_npy_batches("test", batch_size=100)


    # Далее создаем датасеты для TensorFlow
    train_images, train_labels = next(train_generator)  # Загрузим первый батч
    test_images, test_labels = next(test_generator)  # Загрузим первый батч

    print(f"TRAIN: {train_images.shape}, {train_labels.shape}")
    print(f"TEST: {test_images.shape}, {test_labels.shape}")

    # Создаем TensorFlow датасеты
    train_dataset = create_tf_dataset(train_images, train_labels, shuffle=shuffle, augment=augment)
    test_dataset = create_tf_dataset(test_images, test_labels, shuffle=shuffle)

    return train_dataset, test_dataset


if __name__ == "__main__":
    train_ds, test_ds = load_datasets()
    print(test_ds, test_ds)
    print(f"Количество батчей в train_loader: {len(list(train_ds))}")
    print(f"Количество батчей в train_loader: {len(list(test_ds))}")
    print("Датасеты успешно созданы!")
