package api

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"emotions-backend/internal/service"

)

type Handler struct {
	service *service.Service
}

func NewHandler(service *service.Service) *Handler {
	return &Handler{service: service}
}

func (h *Handler) Upload(c *gin.Context) {
	videoPath := c.PostForm("video")
	audioPath := c.PostForm("audio")
	idCandidate := 1 // Заглушка
	idHRManager := 1 // Заглушка

	sessionID, err := h.service.UploadSession(videoPath, audioPath, idCandidate, idHRManager)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"session_id": sessionID})
}

func (h *Handler) GetReport(c *gin.Context) {
	idSession := 1 // Заглушка
	report, err := h.service.GenerateReport(idSession)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, report)
}
