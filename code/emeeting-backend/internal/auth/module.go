package auth

import (
	"github.com/gin-gonic/gin"
)

type Module struct {
	handler *Handler
}

func NewModule() *Module {
	service := NewService()
	return &Module{
		handler: NewHandler(service),
	}
}

func (m *Module) RegisterRoutes(router *gin.Engine) {
	router.POST("/auth/login", m.handler.Login)
	router.POST("/auth/logout", m.handler.Logout)
}
