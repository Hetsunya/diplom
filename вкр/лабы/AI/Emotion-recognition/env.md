

# Использование environment.yml для проекта

## 1. Создание окружения из файла

В корне проекта, где лежит `environment.yml`:

```bash
conda env create -p ./env -f environment.yml
```

* `./env` — папка внутри проекта, где будет создано окружение.

---

## 2. Активация окружения

```bash
conda activate ./env
```

* После активации все Python-скрипты будут использовать нужные версии пакетов.

---

## 3. Проверка окружения

```bash
python - << EOF
import tensorflow as tf
import keras
import h5py
import google.protobuf
print("TF:", tf.__version__)
print("Keras:", keras.__version__)
print("h5py:", h5py.__version__)
print("protobuf:", google.protobuf.__version__)
EOF
```

* Убедись, что версии совпадают с проектными.

---

## 4. Удаление окружения

Если нужно удалить окружение:

```bash
conda deactivate
rm -rf ./env
```
