package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

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
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60,
	}))

	// REST
	r.POST("/sessions", handler.Create)
	r.GET("/sessions", handler.List)
	r.GET("/sessions/:id", handler.Get)

	// auth stubs to match UI contract
	r.POST("/auth/login", func(c *gin.Context) {
		var input struct {
			Email    string `json:"email"`
			Password string `json:"password"`
		}
		if err := c.ShouldBindJSON(&input); err != nil || input.Email == "" || input.Password == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "email and password are required"})
			return
		}

		now := time.Now().UTC().Format(time.RFC3339)
		c.JSON(http.StatusOK, gin.H{
			"authUserId":   1,
			"email":        input.Email,
			"isActive":     true,
			"createdAt":    now,
			"lastLogin":    now,
			"passwordHash": "",
		})
	})
	r.POST("/auth/logout", func(c *gin.Context) {
		c.Status(http.StatusNoContent)
	})

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

	log.Println("Server running on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
