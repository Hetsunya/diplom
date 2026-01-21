package main

import (
	"log"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"emeeting/internal/db"
	"emeeting/internal/session"
)

func main() {
	// DB
	database, err := db.NewPostgres("")
	if err != nil {
		log.Fatal("DB connection failed:", err)
	}

	// session module
	repo := session.NewRepository(database)
	hub := session.NewSessionHub()
	handler := session.NewHandler(repo, hub)

	// gin
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type"},
		AllowCredentials: true,
	}))

	// REST
	r.POST("/sessions", handler.Create)
	r.GET("/sessions", handler.List)

	// WS
	r.GET("/ws/sessions/:id", handler.WS)

	log.Println("Server running on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
