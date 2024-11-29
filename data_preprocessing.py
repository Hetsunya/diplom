import os
import numpy as np
import pandas as pd
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import logging
from config import IMG_SIZE, DATA_DIR, BATCH_SIZE, PROCESSED_DIR, TEST_SIZE

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем директорию для сохранения обработанных данных
os.makedirs(PROCESSED_DIR, exist_ok=True)


def validate_data(data):
    """
    Проверяет корректность данных в CSV: наличие файлов и валидность меток.
    """
    missing_files = [
        row['pth'] for _, row in data.iterrows() if not os.path.exists(os.path.join(DATA_DIR, row['pth']))
    ]
    if missing_files:
        raise ValueError(f"Следующие файлы отсутствуют: {missing_files}")
    logger.info("Все файлы найдены и доступны.")


def process_batch(batch, label_mapping):
    """
    Обрабатывает батч данных, возвращая изображения и метки.
    """
    images = []
    labels = []

    for _, row in batch.iterrows():
        img_path = os.path.join(DATA_DIR, row['pth'])
        try:
            # Загружаем и изменяем размер изображения
            img = load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
            img_array = img_to_array(img) / 255.0  # Нормализация
            images.append(img_array.astype(np.float32))  # Используем float32
            labels.append(label_mapping[row['label']])
        except Exception as e:
            logger.error(f"Ошибка обработки {img_path}: {e}")

    return np.array(images), np.array(labels, dtype=np.int32)  # Используем int32 для меток


def save_data_as_npy_batched():
    """
    Загружает данные, делит на train/test и сохраняет в .npy файлы батчами.
    """
    logger.info("Загрузка данных из CSV...")
    data = pd.read_csv(os.path.join(DATA_DIR, 'labels.csv'))

    # Проверяем данные
    validate_data(data)

    # Маппинг меток
    label_mapping = {label: idx for idx, label in enumerate(data['label'].unique())}
    logger.info(f"Маппинг меток: {label_mapping}")

    # Делим данные на train/test
    train_data, test_data = train_test_split(
        data, test_size=TEST_SIZE, random_state=42, stratify=data['label']
    )

    # Сохраняем train батчи
    logger.info("Обработка и сохранение TRAIN данных...")
    for i, start_idx in tqdm(enumerate(range(0, len(train_data), BATCH_SIZE)), total=len(train_data) // BATCH_SIZE):
        batch = train_data.iloc[start_idx:start_idx + BATCH_SIZE]
        images, labels = process_batch(batch, label_mapping)
        if len(images) > 0:  # Сохраняем только непустые батчи
            np.save(os.path.join(PROCESSED_DIR, f'X_train_batch_{i}.npy'), images)
            np.save(os.path.join(PROCESSED_DIR, f'y_train_batch_{i}.npy'), labels)
            logger.info(f"Сохранен TRAIN батч {i}: {images.shape}, {labels.shape}")

    # Сохраняем test батчи
    logger.info("Обработка и сохранение TEST данных...")
    for i, start_idx in tqdm(enumerate(range(0, len(test_data), BATCH_SIZE)), total=len(test_data) // BATCH_SIZE):
        batch = test_data.iloc[start_idx:start_idx + BATCH_SIZE]
        images, labels = process_batch(batch, label_mapping)
        if len(images) > 0:  # Сохраняем только непустые батчи
            np.save(os.path.join(PROCESSED_DIR, f'X_test_batch_{i}.npy'), images)
            np.save(os.path.join(PROCESSED_DIR, f'y_test_batch_{i}.npy'), labels)
            logger.info(f"Сохранен TEST батч {i}: {images.shape}, {labels.shape}")

    logger.info("Все данные сохранены!")


if __name__ == "__main__":
    save_data_as_npy_batched()
