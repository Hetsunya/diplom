import cv2
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import torchvision.models as models

# Если у вас есть GPU, используйте его
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


MODEL_PATH = "best_model.pth"  # Файл с обученной моделью
CLASS_NAMES = ['anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']  # Классы

# Загрузим модель
model = models.resnet18(weights=None)  # Создаём модель
model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))  # Меняем последний слой
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))  # Загружаем веса
model = model.to(device)
model.eval()  # Переводим в режим предсказания

model.to(device)

# Преобразования для входных данных
transform = transforms.Compose([
    transforms.Resize((96, 96)),  # Приводим изображение к нужному размеру
    transforms.ToTensor(),  # Преобразуем в тензор
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # Нормализация
])

# Инициализируем захват видео с веб-камеры
cap = cv2.VideoCapture(0)  # 0 - это номер встроенной веб-камеры

# Загрузка классификатора Хаара для обнаружения лиц
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Список классов для вывода
class_names = ['anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

while True:
    # Чтение кадра с веб-камеры
    ret, frame = cap.read()

    if not ret:
        print("Не удалось захватить кадр с камеры.")
        break

    # Преобразуем изображение в формат, который принимает модель
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))


    # Если лицо обнаружено
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # Вырезаем лицо из кадра
            face_image = frame[y:y+h, x:x+w]
            image = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
            image = transform(image).unsqueeze(0)  # Добавляем размерность батча

            # Переносим на устройство (GPU/CPU)
            image = image.to(device)

            # Предсказание
            with torch.no_grad():  # Отключаем градиенты
                outputs = model(image)
                _, predicted = torch.max(outputs, 1)
                predicted_class = predicted.item()

            # Отображаем результат на экране
            label = class_names[predicted_class]
            cv2.putText(frame, f"Prediction: {label}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Рисуем прямоугольник вокруг лица
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Показываем кадр
    cv2.imshow('Emotion Detection', frame)

    # Выход из цикла при нажатии на клавишу 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
