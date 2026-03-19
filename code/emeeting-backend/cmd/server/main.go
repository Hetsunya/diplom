package main

import (
	"log"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"emeeting/internal/auth"
	"emeeting/internal/db"
	"emeeting/internal/reports"
	"emeeting/internal/server"
	"emeeting/internal/session"
	"emeeting/internal/ws"
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

	// gin
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{corsOrigin},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60,
	}))

	modules := []server.RouteModule{
		auth.NewModule(),
		session.NewModule(database),
		reports.NewModule(),
		ws.NewModule(),
	}
	for _, module := range modules {
		module.RegisterRoutes(r)
	}

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
