package api

import "github.com/gin-gonic/gin"

func SetupRoutes(r *gin.Engine, h *Handler) {
	r.POST("/upload", h.Upload)
	r.GET("/report", h.GetReport)
}
