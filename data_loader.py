import os
import numpy as np
import tensorflow as tf
from config import PROCESSED_DIR, BATCH_SIZE, IMG_SIZE
# Константы
AUTO = tf.data.AUTOTUNE  # Автоматическая настройка для параллельной загрузки данных


def load_npy_batches(data_type):
    """
    Загружает данные (train или test) из .npy файлов.

    :param data_type: Тип данных ('train' или 'test').
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
        images.append(np.load(img_path))  # Загружаем изображения
        labels.append(np.load(lbl_path))  # Загружаем метки

    # Конкатенируем все батчи в один массив
    return np.concatenate(images, axis=0), np.concatenate(labels, axis=0)


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


def load_datasets(shuffle, augment):
    """
    Загружает данные из обработанных файлов и создает tf.data.Dataset.

    :param shuffle: Если True, данные будут перемешаны.
    :param augment: Если True, применяются аугментации.
    :return: Кортеж (train_dataset, test_dataset).
    """
    print("Загрузка TRAIN данных...")
    train_images, train_labels = load_npy_batches("train")
    print(f"TRAIN: {train_images.shape}, {train_labels.shape}")

    print("Загрузка TEST данных...")
    test_images, test_labels = load_npy_batches("test")
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
