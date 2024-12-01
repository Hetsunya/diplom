import os
import tensorflow as tf
from config import PROCESSED_DIR, BATCH_SIZE, IMG_SIZE

# Константы
AUTO = tf.data.AUTOTUNE  # Автоматическая настройка для параллельной загрузки данных


def parse_tfrecord(tfrecord):
    """
    Парсинг одного примера из файла .tfrecord.
    :param tfrecord: Строка данных в формате .tfrecord
    :return: Изображение и метка.
    """
    # Описание структуры записи
    feature_description = {
        'image': tf.io.FixedLenFeature([], tf.string),  # Изображение как строка
        'label': tf.io.FixedLenFeature([1], tf.int64),  # Метка как целое число
    }

    # Парсинг записи
    parsed_features = tf.io.parse_single_example(tfrecord, feature_description)

    # Декодирование изображения
    image = tf.io.decode_jpeg(parsed_features['image'], channels=3)
    image = tf.image.resize(image, [IMG_SIZE, IMG_SIZE])  # Размер изображения

    # Нормализация изображения
    image = tf.cast(image, tf.float32) / 255.0

    label = parsed_features['label'][0]  # Метка

    return image, label


def advanced_augmentation(image, label):
    """
    Расширенная аугментация данных для изображений.
    :param image: Изображение.
    :param label: Метка.
    :return: Преобразованные данные.
    """
    # Преобразования на уровне геометрии
    image = tf.image.random_flip_left_right(image)  # Горизонтальное отражение
    image = tf.image.random_flip_up_down(image)  # Вертикальное отражение

    # Пространственные преобразования
    image = tf.image.resize_with_crop_or_pad(image, IMG_SIZE + 10, IMG_SIZE + 10)
    image = tf.image.random_crop(image, size=[IMG_SIZE, IMG_SIZE, 3])  # Уменьшение

    # Добавляем случайный шум
    noise = tf.random.normal(shape=tf.shape(image), mean=0.0, stddev=0.1, dtype=image.dtype)  # Совместим с типом image
    image = tf.add(image, noise)

    # Обрезаем значения для корректного диапазона [0, 1]
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image, label


def load_tfrecord_files(file_pattern):
    """
    Загружает файлы .tfrecord с указанным паттерном.
    :param file_pattern: Паттерн для поиска файлов .tfrecord.
    :return: tf.data.Dataset, содержащий данные из .tfrecord.
    """
    # Считываем файлы .tfrecord
    files = [os.path.join(PROCESSED_DIR, file) for file in os.listdir(PROCESSED_DIR) if file.endswith('.tfrecord')]
    raw_dataset = tf.data.TFRecordDataset(files)

    # Применяем парсинг для каждого файла
    dataset = raw_dataset.map(parse_tfrecord, num_parallel_calls=AUTO)

    return dataset


def create_tf_dataset(dataset, shuffle=True, augment=False):
    """
    Создает tf.data.Dataset для подачи в модель.

    :param dataset: Загруженный tf.data.Dataset.
    :param shuffle: Если True, данные будут перемешаны.
    :param augment: Если True, применяются аугментации.
    :return: tf.data.Dataset.
    """
    if shuffle:
        dataset = dataset.shuffle(buffer_size=10000)

    if augment:
        dataset = dataset.map(advanced_augmentation, num_parallel_calls=AUTO)

    dataset = dataset.batch(BATCH_SIZE).prefetch(AUTO)

    return dataset


def load_datasets(shuffle=True, augment=False):
    """
    Загружает данные из обработанных .tfrecord файлов и создает tf.data.Dataset.

    :param shuffle: Если True, данные будут перемешаны.
    :param augment: Если True, применяются аугментации.
    :return: Кортеж (train_dataset, val_dataset).
    """
    print("Загрузка TRAIN данных...")
    train_dataset = load_tfrecord_files("train")  # Загружаем TRAIN данные

    print("Загрузка VAL данных...")
    val_dataset = load_tfrecord_files("val")  # Загружаем VAL данные

    print(f"TRAIN: {train_dataset}")
    print(f"VAL: {val_dataset}")

    # Создаем TensorFlow датасеты
    train_dataset = create_tf_dataset(train_dataset, shuffle=shuffle, augment=augment)
    val_dataset = create_tf_dataset(val_dataset, shuffle=shuffle)

    return train_dataset, val_dataset


if __name__ == "__main__":
    train_ds, val_ds = load_datasets(augment=True)
    print(f"Количество батчей в train_loader: {len(list(train_ds))}")
    print(f"Количество батчей в val_loader: {len(list(val_ds))}")
    print("Датасеты успешно созданы!")
