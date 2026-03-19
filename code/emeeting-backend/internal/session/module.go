package session

import (
	"database/sql"

	"github.com/gin-gonic/gin"
)

type Module struct {
	handler *Handler
}

func NewModule(database *sql.DB) *Module {
	repo := NewRepository(database)
	service := NewService(repo)
	hub := NewSessionHub()
	return &Module{
		handler: NewHandler(service, hub),
	}
}

func (m *Module) RegisterRoutes(router *gin.Engine) {
	router.POST("/sessions", m.handler.Create)
	router.GET("/sessions", m.handler.List)
	router.GET("/sessions/:id", m.handler.Get)
	router.GET("/ws/sessions/:id", m.handler.WS)
}
