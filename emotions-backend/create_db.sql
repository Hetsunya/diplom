-- Создание базы данных
CREATE DATABASE emotions;

-- Подключение к базе данных
\c emotions

-- Создание таблицы HR_Manager
CREATE TABLE HR_Manager (
    id_hr_manager SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Создание таблицы Candidate
CREATE TABLE Candidate (
    id_candidate SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(100)
);

-- Создание таблицы Session
CREATE TABLE Session (
    id_session SERIAL PRIMARY KEY,
    id_candidate INTEGER NOT NULL REFERENCES Candidate(id_candidate),
    id_hr_manager INTEGER NOT NULL REFERENCES HR_Manager(id_hr_manager),
    date_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    video VARCHAR(255),  -- Путь к видеофайлу
    audio VARCHAR(255)   -- Путь к аудиофайлу
);

-- Создание таблицы Emotions
CREATE TABLE Emotions (
    id_emotion SERIAL PRIMARY KEY,
    id_session INTEGER NOT NULL REFERENCES Session(id_session),
    emotion VARCHAR(50) NOT NULL,
    probability FLOAT NOT NULL CHECK (probability >= 0 AND probability <= 1)
);

-- Создание таблицы Report
CREATE TABLE Report (
    id_report SERIAL PRIMARY KEY,
    id_session INTEGER NOT NULL UNIQUE REFERENCES Session(id_session),
    id_hr_manager INTEGER NOT NULL REFERENCES HR_Manager(id_hr_manager),
    metrics TEXT NOT NULL,  -- JSON или текст со статистикой
    summary TEXT NOT NULL
);

-- Создание таблицы Features
CREATE TABLE Features (
    id_feature SERIAL PRIMARY KEY,
    id_session INTEGER NOT NULL REFERENCES Session(id_session),
    facial_features JSONB,  -- Координаты ключевых точек лица
    mfcc JSONB             -- Мел-частотные кепстральные коэффициенты
);

-- Создание индексов для оптимизации
CREATE INDEX idx_session_id_candidate ON Session(id_candidate);
CREATE INDEX idx_session_id_hr_manager ON Session(id_hr_manager);
CREATE INDEX idx_emotions_id_session ON Emotions(id_session);
CREATE INDEX idx_features_id_session ON Features(id_session);