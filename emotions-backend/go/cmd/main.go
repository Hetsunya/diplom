package main

import (
	"database/sql"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"go.uber.org/zap"

	"emotions-backend/config"
	"emotions-backend/internal/api"
	"emotions-backend/internal/repository"
	"emotions-backend/internal/service"
	"emotions-backend/internal/utils"
)

func main() {
	cfg := config.LoadConfig()
	logger := utils.NewLogger()
	defer logger.Sync()

	db, err := sql.Open("postgres", cfg.DatabaseURL)
	if err != nil {
		logger.Fatal("Failed to connect to database", zap.Error(err))
	}
	defer db.Close()

	repo := repository.NewRepository(db)
	svc := service.NewService(repo, cfg.PythonAPI)
	handler := api.NewHandler(svc)

	r := gin.Default()
	api.SetupRoutes(r, handler)

	logger.Info("Starting server", zap.String("port", cfg.ServerPort))
	if err := r.Run(cfg.ServerPort); err != nil {
		logger.Fatal("Failed to start server", zap.Error(err))
	}
}
