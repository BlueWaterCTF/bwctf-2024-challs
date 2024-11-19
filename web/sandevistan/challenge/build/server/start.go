package server

import (
	db "Sandevistan/database"
	"Sandevistan/utils"
	"Sandevistan/models"

	"net/http"
	"path/filepath"
	"database/sql"
	
	"github.com/gorilla/mux"
)

/* --------- HTTP server --------- */
type Server struct {
	dbClient *sql.DB
	Users map[string]*models.User
}



func NewServer() *Server {
	database, err := db.Init()
	if err != nil {
		panic(err)
	}
	users := make(map[string]*models.User, 20)
	s := &Server{
		dbClient: database,
		Users: users,
	}
	cyberwares := make(map[string]models.CyberWare, 0)
	errs := make([]*models.UserError, 0)
	nouser := &models.User{
		Name: "NOUSER",
		Augments: cyberwares,
		Errors: errs,
	}
	s.AppendToUsers(nouser)
	return s
}

func root(w http.ResponseWriter, r *http.Request){
	http.ServeFile(w, r, "./tmpl/index.html")
}

func (s *Server) Serve() error {
	r := mux.NewRouter()
	path := filepath.Join(utils.GetCwd(), "static")

	r.PathPrefix("/static/").Handler(http.StripPrefix("/static", http.FileServer(http.Dir(path))))
	r.HandleFunc("/", root)
	r.HandleFunc("/cyberware", s.cwHandleGet).Methods("GET")
	r.HandleFunc("/cyberware", s.cwHandlePost).Methods("POST")
	r.HandleFunc("/user", s.handleUserGet).Methods("GET")
	r.HandleFunc("/user", s.handleUserPost).Methods("POST")
    return http.ListenAndServe(":8080", r)
}

