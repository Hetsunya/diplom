import torch
import torchvision.transforms as transforms
import torchvision.models as models
import cv2
import numpy as np
from PIL import Image

# Пути
# MODEL_PATH = "emotion_model.pth"  # Файл с обученной моделью
MODEL_PATH = "best_model.pth"  # Файл с обученной моделью
CLASS_NAMES = ['anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']  # Классы

# Проверяем устройство
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Используется устройство: {device}")

# Загружаем модель
model = models.resnet18(weights=None)  # Создаём модель
model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))  # Меняем последний слой
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))  # Загружаем веса
model = model.to(device)
model.eval()  # Переводим в режим предсказания


# Функция предсказания
def predict_emotion(image_path):
    # Загружаем изображение
    img = Image.open(image_path).convert("RGB")

    # Преобразования, как при обучении
    transform = transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    img_tensor = transform(img).unsqueeze(0).to(device)  # Добавляем batch dimension

    # Предсказание
    with torch.no_grad():
        output = model(img_tensor)
        _, predicted = torch.max(output, 1)

    emotion = CLASS_NAMES[predicted.item()]
    return emotion


# Проверка на примере
image_path = "test/img_9.png"  # Замените на путь к вашему изображению
emotion = predict_emotion(image_path)
print(f"🟢 Предсказанная эмоция: {emotion}")
