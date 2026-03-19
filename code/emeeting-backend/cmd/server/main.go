package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"emeeting/internal/auth"
	"emeeting/internal/db"
	"emeeting/internal/session"
	wsmodule "emeeting/internal/ws"
)

func main() {
	postgresDSN := getEnv("POSTGRES_DSN", "postgres://postgres:1040@localhost:5432/emeeting?sslmode=disable")
	serverPort := getEnv("SERVER_PORT", "8080")
	corsOrigin := getEnv("CORS_ALLOW_ORIGIN", "http://localhost:5173")

	// DB
	database, err := db.NewPostgres(postgresDSN)
	if err != nil {
		log.Fatal("DB connection failed:", err)
	}

	// session module
	repo := session.NewRepository(database)
	sessionService := session.NewService(repo)
	hub := session.NewSessionHub()
	handler := session.NewHandler(sessionService, hub)
	authHandler := auth.NewHandler(auth.NewService())
	wsHandler := wsmodule.NewHandler()

	// gin
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{corsOrigin},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60,
	}))

	// REST
	r.POST("/sessions", handler.Create)
	r.GET("/sessions", handler.List)
	r.GET("/sessions/:id", handler.Get)

	// auth
	r.POST("/auth/login", authHandler.Login)
	r.POST("/auth/logout", authHandler.Logout)

	// report stub to match UI contract
	r.GET("/reports/:id", func(c *gin.Context) {
		id := c.Param("id")
		c.JSON(http.StatusOK, gin.H{
			"reportId":   id,
			"sessionId":  id,
			"version":    1,
			"createdAt":  time.Now().UTC().Format(time.RFC3339),
			"updatedAt":  time.Now().UTC().Format(time.RFC3339),
			"summaryJson": gin.H{
				"status": "stub",
				"note":   fmt.Sprintf("Report %s is not generated yet", id),
			},
		})
	})

	// WS
	r.GET("/ws/sessions/:id", handler.WS)
	r.GET("/ws/health", wsHandler.Health)

	addr := ":" + serverPort
	log.Printf("Server running on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}

func getEnv(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
