import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.utils.data import DataLoader, random_split
from torchvision import models
import os
from tqdm import tqdm  # Импортируем tqdm
import time

PAUSE_TIME = 30
CHECKPOINT_PATH = "checkpoint.pth"


# Проверяем, есть ли GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Используется устройство: {device}")

# Пути к данным
DATASET_PATH = "../data"
BATCH_SIZE = 8
IMG_SIZE = 96
EPOCHS = 10

# Аугментация данных
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Загрузка данных
full_dataset = datasets.ImageFolder(root=DATASET_PATH, transform=transform)

# Разделение данных на тренировочную и валидационную выборку
train_size = int(0.8 * len(full_dataset))  # 80% для тренировки
val_size = len(full_dataset) - train_size  # Остальные 20% для валидации
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

# Получаем количество классов
num_classes = len(full_dataset.classes)
print(f"🟢 Найдено {num_classes} классов: {full_dataset.classes}")

# Загружаем предобученную ResNet-18
model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
model.fc = nn.Linear(model.fc.in_features, num_classes)  # Заменяем выходной слой
model = model.to(device)

# Функция потерь и оптимизатор
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Обучение модели
print("🚀 Начинаем обучение...")
best_accuracy = 0.0  # Лучшая точность
patience = 3  # Количество эпох без улучшения перед остановкой
epochs_no_improve = 0  # Счётчик эпох без улучшения

for epoch in range(EPOCHS):
    # Обучение
    model.train()
    train_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(train_loader, desc=f"Эпоха {epoch + 1}/{EPOCHS}", ncols=100):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    train_accuracy = 100 * correct / total
    print(f"📌 Эпоха {epoch + 1}/{EPOCHS} - Потери: {train_loss / len(train_loader):.4f}, Точность: {train_accuracy:.2f}%")

    # Валидация
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            val_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    val_accuracy = 100 * correct / total
    print(f"📌 Эпоха {epoch + 1}/{EPOCHS} - Валидация - Потери: {val_loss / len(val_loader):.4f}, Точность: {val_accuracy:.2f}%")

    # Сохраняем после каждой эпохи
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': train_loss,
    }, CHECKPOINT_PATH)

    # Проверяем, стала ли точность лучше
    if val_accuracy > best_accuracy:
        best_accuracy = val_accuracy
        torch.save(model.state_dict(), "best_model.pth")  # Сохраняем
        print("✅ Новая лучшая модель сохранена!")
        epochs_no_improve = 0
    else:
        epochs_no_improve += 1
        print(f"⚠️ Нет улучшений ({epochs_no_improve}/{patience})")

    # Если нет улучшений 3 эпохи подряд — останавливаем обучение
    if epochs_no_improve >= patience:
        print("🛑 Раннее завершение обучения (Early Stopping)")
        break

    print(f"⏸️ Перерыв {PAUSE_TIME//60} минут для охлаждения GPU...")
    time.sleep(PAUSE_TIME)


# Сохранение модели
torch.save(model.state_dict(), "emotion_model.pth")
print("✅ Обучение завершено, модель сохранена!")
