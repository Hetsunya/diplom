package reports

import (
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type Module struct{}

func NewModule() *Module {
	return &Module{}
}

func (m *Module) RegisterRoutes(router *gin.Engine) {
	router.GET("/reports/:id", func(c *gin.Context) {
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
}
