package analysis

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type HTTPHandler struct {
	svc *Service
}

func NewHTTPHandler(svc *Service) *HTTPHandler {
	return &HTTPHandler{svc: svc}
}

func (h *HTTPHandler) GetReport(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session id"})
		return
	}
	raw, err := h.svc.GetLatestReportJSON(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if raw == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no report yet"})
		return
	}
	c.Data(http.StatusOK, "application/json", raw)
}

func (h *HTTPHandler) ListEvents(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session id"})
		return
	}
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	raw, err := h.svc.ListEventsJSON(c.Request.Context(), id, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.Data(http.StatusOK, "application/json", raw)
}
