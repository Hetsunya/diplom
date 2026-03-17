package db

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/lib/pq"
)

func NewPostgres(dsn string) (*sql.DB, error) {
	db, err := sql.Open(
		"postgres",
		"postgres://postgres:1040@localhost:5432/emeeting?sslmode=disable",
	)
	if err != nil {
		log.Fatal(err)
	}

	if err := db.Ping(); err != nil {
		return nil, err
	}

	fmt.Println("PostgreSQL connected")
	return db, nil
}
