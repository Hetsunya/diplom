package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	DatabaseURL string
	ServerPort  string
	PythonAPI   string // URL для Python (Flask)
}

func LoadConfig() *Config {
	err := godotenv.Load()
	if err != nil {
		log.Println("No .env file found, using default values")
	}

	return &Config{
		DatabaseURL: getEnv("DATABASE_URL", "user=postgres password=pass dbname=emotions sslmode=disable"),
		ServerPort:  getEnv("SERVER_PORT", ":8080"),
		PythonAPI:   getEnv("PYTHON_API", "http://localhost:5000/analyze"),
	}
}

func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
