# Конфигурация проекта

# Пути к данным
DATA_DIR = '../data'  # Папка с изображениями и CSV
PROCESSED_DIR = 'processed_data'  # Папка для сохранения .npy
MODEL_DIR = './models'
MODEL = "./model/final_model.keras"
BEST_MODEL = "./model/checkpoints/best_model.keras"
DATASET_PATH = "../data"


#Если изменить labels.csv то могут поменяться!!!
label_mapping = {
    'surprise': 0,
    'anger': 1,
    'disgust': 2,
    'fear': 3,
    'sad': 4,
    'contempt': 5,
    'neutral': 6,
    'happy': 7
}

# Гиперпараметры
IMG_SIZE = 48  # Размер изображений
BATCH_SIZE = 16
EPOCHS = 100
LEARNING_RATE = 1e-5
TEST_SIZE = 0.2
LABELS = 8