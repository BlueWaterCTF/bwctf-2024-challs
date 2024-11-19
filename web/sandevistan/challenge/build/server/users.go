package server

import (
	"Sandevistan/models"
	"Sandevistan/utils"

	"net/http"
	"errors"
	"fmt"
	"context"
)

func (s *Server) AppendToUsers(u *models.User) {
	s.Users[u.Name] = u
}

func (s *Server) GetUser(username string) (*models.User, error) {
	user, exists := s.Users[username]
	if !exists {
		return nil, errors.New("user not found")
	}
	return user, nil
}

func (s *Server) handleUserPost(w http.ResponseWriter, r *http.Request) {
	u, uerr := s.GetUser(r.FormValue("username"))
	if uerr != nil {
		ctx := r.Context()
		ctx = context.WithValue(ctx, "username", "NOUSER")
		username := r.FormValue("username")
		ue := utils.AlphaNumCheck(ctx, username)
		if ue != nil {
			http.Error(w, "BAD CHARACTERS IN USERNAME", http.StatusBadRequest)
			return
		}
		cyberwares := make(map[string]models.CyberWare, 0)
		errs := make([]*models.UserError, 0)
		u = &models.User{
			Name: r.FormValue("username"),
			Augments: cyberwares,
			Errors: errs,
		}
		s.AppendToUsers(u)
		fmt.Println(s.Users)
	}
	http.Redirect(w, r, "/user", http.StatusFound)
}

func (s *Server) handleUserGet(w http.ResponseWriter, r *http.Request) {
	u, err := s.GetUser(r.FormValue("username"))
	if err != nil {
		http.Error(w, "Username not found", http.StatusNotFound)
		return
	}

	if u.Name == "NOUSER" {
		http.Redirect(w, r, "/", http.StatusFound)
	}
	utils.RenderTemplate(w, "/tmpl/user", u)
}