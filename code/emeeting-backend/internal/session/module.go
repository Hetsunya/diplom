package session

import (
	"database/sql"

	"github.com/gin-gonic/gin"

	"emeeting/internal/analysis"
)

type Module struct {
	handler *Handler
}

func NewModule(database *sql.DB) *Module {
	repo := NewRepository(database)
	service := NewService(repo)
	hub := NewSessionHub()
	analysisSvc := analysis.NewService(database)
	return &Module{
		handler: NewHandler(service, hub, analysisSvc),
	}
}

func (m *Module) RegisterRoutes(router *gin.Engine) {
	router.POST("/sessions", m.handler.Create)
	router.GET("/sessions", m.handler.List)
	router.GET("/sessions/:id", m.handler.Get)
	router.GET("/ws/sessions/:id", m.handler.WS)
}
