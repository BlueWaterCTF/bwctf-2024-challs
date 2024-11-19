package server

import (
	"Sandevistan/utils"
	"Sandevistan/database"
	"Sandevistan/models"
	"net/http"
	"math/rand/v2"
	"context"
)

func (s *Server) cwHandleGet(w http.ResponseWriter, r *http.Request){
	ctx := r.Context()
	single := r.FormValue("cyberware")
	if single != "" {
		ware, serr := db.GetCyberWare(s.dbClient, ctx, single)
		if serr != nil {
			http.Error(w, serr.Error(), http.StatusNotFound)
			return
		}
		utils.RenderTemplate(w, "/tmpl/cyberware", ware)
		return
	}
	http.Error(w, "Please specify a CyberWare", http.StatusBadRequest)
	return
}

func checkForm(r *http.Request) *models.UserError {
	var ue *models.UserError
	ctx := r.Context()
	username, exists := r.Form["username"]
	if !exists {
		ue = &models.UserError{
			Value: "NOUSER",
			Filename: "nouser",
			Ctx: ctx,
		}
		return ue
	}
	ctx = context.WithValue(ctx, "username", username[len(username)-1])
	cwName, exists := r.Form["name"]
	if !exists {
		ue = utils.ErrorFactory(ctx, "CyberWare name doesn't exist", username[len(username)-1])
		return ue
	}
	ue = utils.AlphaNumCheck(ctx, cwName[0])
	return ue
}

func (s *Server) cwHandlePost(w http.ResponseWriter, r *http.Request){
	err := r.ParseForm()
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	ue := checkForm(r)
	username := r.PostForm["username"]
	user, uerr := s.GetUser(username[len(username)-1])
	if uerr != nil {
		user, _ = s.GetUser("NOUSER")
	}
	if ue != nil { 
		user.AddError(ue)
		http.Error(w, "BAD REQUEST", http.StatusBadRequest)
		return
	}
	name:= r.PostForm["name"]

	cw := models.CyberWare{
		Name: name[len(name)-1],
		BaseQuality: rand.IntN(10), 
		Capacity: rand.IntN(10),
		Iconic: false,
		Username: username[len(username)-1],
	}
	_, cerr := db.InsertCyberware(s.dbClient, cw)
	if cerr != nil {
		http.Error(w, cerr.Error(), http.StatusInternalServerError)
		return
	}
	user.AddCyberWare(cw)
	http.Redirect(w, r, "/cyberware", http.StatusFound)
}
