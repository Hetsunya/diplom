package session

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"emeeting/internal/models"
)

type Handler struct {
	repo *Repository
	hub  *SessionHub
}

func NewHandler(repo *Repository, hub *SessionHub) *Handler {
	return &Handler{repo: repo, hub: hub}
}

// DTO для создания сессии
type CreateSessionDTO struct {
	Title            string               `json:"title" binding:"required"`
	SessionType      models.SessionType   `json:"sessionType" binding:"required"`
	StartDatetime    string               `json:"startDatetime" binding:"required"`
	EndDatetime      *string              `json:"endDatetime,omitempty"`
	Description      *string              `json:"description,omitempty"`
	LocationType     *models.LocationType `json:"locationType,omitempty"`
	PhysicalLocation *string              `json:"physicalLocation,omitempty"`
}

// Create создает новую сессию
func (h *Handler) Create(c *gin.Context) {
	var input CreateSessionDTO
	if err := c.ShouldBindJSON(&input); err != nil {
		log.Printf("ERROR: binding JSON: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	startTime, err := time.Parse("2006-01-02T15:04", input.StartDatetime)
	if err != nil {
		log.Printf("ERROR: parsing startDatetime: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid startDatetime format"})
		return
	}

	var endTime *time.Time
	if input.EndDatetime != nil && *input.EndDatetime != "" {
		t, err := time.Parse("2006-01-02T15:04", *input.EndDatetime)
		if err != nil {
			log.Printf("ERROR: parsing endDatetime: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid endDatetime format"})
			return
		}
		endTime = &t
	}

	session := models.Session{
		Title:            input.Title,
		SessionType:      input.SessionType,
		StartDatetime:    &startTime,
		EndDatetime:      endTime,
		Description:      input.Description,
		LocationType:     input.LocationType,
		PhysicalLocation: input.PhysicalLocation,
		CreatedBy:        ptrInt(1), // временно админский ID
	}

	log.Printf("DEBUG: creating session %+v", session)
	id, err := h.repo.Create(session)
	if err != nil {
		log.Printf("ERROR: failed to create session: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	session.SessionID = id
	c.JSON(http.StatusCreated, session)
}

func (h *Handler) List(c *gin.Context) {
	sessions, err := h.repo.List()
	if err != nil {
		log.Printf("ERROR: failed to list sessions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, sessions)
}

func (h *Handler) Get(c *gin.Context) {
	idParam := c.Param("id")
	var id int
	_, err := fmt.Sscanf(idParam, "%d", &id)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	session, err := h.repo.Get(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "session not found"})
		return
	}

	c.JSON(http.StatusOK, session)
}

func ptrInt(v int) *int { return &v }
