package main

import (
	"log"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"emeeting/internal/db"
	"emeeting/internal/session"
)

func main() {
	// Подключаемся через твой модуль
	database, err := db.NewPostgres("") // DSN внутри db.NewPostgres уже захардкожен
	if err != nil {
		log.Fatal("DB connection failed:", err)
	}

	// Репозиторий и хендлер сессий
	repo := session.NewRepository(database)
	handler := session.NewHandler(repo)

	// Настройка Gin
	r := gin.Default()

	// CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type"},
		AllowCredentials: true,
	}))

	// Роуты API
	r.POST("/sessions", handler.Create)
	r.GET("/sessions", handler.List)

	log.Println("Server running on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
