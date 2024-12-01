import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tqdm import tqdm
import logging
from config import IMG_SIZE, DATA_DIR, PROCESSED_DIR

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем директорию для сохранения обработанных данных
os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_data_from_folder(folder_path):
    """
    Сканирует папку и возвращает список изображений с их метками.
    """
    data = []
    class_names = sorted(os.listdir(folder_path))
    label_mapping = {cls: idx for idx, cls in enumerate(class_names)}

    for class_name in class_names:
        class_path = os.path.join(folder_path, class_name)
        if not os.path.isdir(class_path):
            continue

        for img_name in os.listdir(class_path):
            img_path = os.path.join(class_name, img_name)  # Здесь изменено на правильный путь
            data.append({'pth': img_path, 'label': label_mapping[class_name]})

    logger.info(f"Найдено {len(data)} изображений в {len(class_names)} классах.")
    return data, label_mapping


def serialize_example(image, label):
    """
    Сериализация изображения и метки в формат TFRecord.
    """
    feature = {
        'image': tf.train.Feature(bytes_list=tf.train.BytesList(value=[tf.io.encode_jpeg(image).numpy()])),
        'label': tf.train.Feature(int64_list=tf.train.Int64List(value=[label]))
    }
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()

def write_tfrecord(data, base_dir, output_path):
    """
    Сохранение данных в TFRecord файл.
    """
    with tf.io.TFRecordWriter(output_path) as writer:
        for entry in tqdm(data, desc=f"Сохранение в {output_path}"):
            img_path = entry['pth']
            label = entry['label']
            try:
                # Загружаем и изменяем размер изображения
                img = load_img(os.path.join(base_dir, img_path), target_size=(IMG_SIZE, IMG_SIZE))
                img_array = img_to_array(img).astype('uint8')  # Не нормализуем для TFRecord
                serialized_example = serialize_example(tf.convert_to_tensor(img_array), label)
                writer.write(serialized_example)
            except Exception as e:
                logger.error(f"Ошибка обработки {img_path}: {e}")

if __name__ == "__main__":
    # Пути к папкам train и val
    train_path = os.path.join(DATA_DIR, "train_class")
    val_path = os.path.join(DATA_DIR, "val_class")

    # Обработка TRAIN данных
    logger.info("Начало обработки TRAIN данных...")
    train_data, train_label_mapping = get_data_from_folder(train_path)
    train_output_path = os.path.join(PROCESSED_DIR, 'train.tfrecord')
    write_tfrecord(train_data, train_path, train_output_path)
    logger.info("TRAIN данные сохранены.")

    # Обработка VAL данных
    logger.info("Начало обработки VAL данных...")
    val_data, val_label_mapping = get_data_from_folder(val_path)
    val_output_path = os.path.join(PROCESSED_DIR, 'val.tfrecord')
    write_tfrecord(val_data, val_path, val_output_path)
    logger.info("VAL данные сохранены.")

    logger.info("Обработка завершена.")
