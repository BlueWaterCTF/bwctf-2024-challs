package db

import (
	"Sandevistan/models"
	
	"context"
	"fmt"

	"database/sql"
	_"github.com/mattn/go-sqlite3"
)


func Init() (*sql.DB, error) {
	db, err := sql.Open("sqlite3", "cyberpunk.db")
	if err != nil {
		return nil,err
	   }
	perr := db.Ping()
	if perr != nil {
		return nil, perr
	}

	create := fmt.Sprintf(`
	CREATE TABLE IF NOT EXISTS cyberware (
	name 		STRING NOT NULL PRIMARY KEY UNIQUE,
	baseQuality INT,
	capacity 	INT,
	iconic 		BOOLEAN,
	username	STRING
	);
	`)
	if _, err := db.Exec(create); err != nil {
		return nil, err
	}

	return db, nil
}

func InsertCyberware(db *sql.DB, cw models.CyberWare) (int, error){
	res, err := db.Exec("INSERT INTO cyberware VALUES (?, ?, ?, ?, ?)", cw.Name, cw.BaseQuality, cw.Capacity, cw.Iconic, cw.Username)
	if err != nil {
		return 0, err
	   }
	var id int64
	if id, err = res.LastInsertId(); err != nil {
		return 0, err
		}
	return int(id), nil
}

func GetCyberWare(db *sql.DB, ctx context.Context, name string) (models.CyberWare, error){
	row, qerr := db.QueryContext(ctx, "SELECT * FROM cyberware WHERE name = ?", name)

	cyberware := models.CyberWare{}

	if qerr != nil {
		return cyberware, qerr
	}

	var err error
	if err = row.Scan(&cyberware.Name, &cyberware.BaseQuality, &cyberware.Capacity, &cyberware.Iconic); 
		err == sql.ErrNoRows {
			return cyberware, err
	}
	return cyberware, nil
}