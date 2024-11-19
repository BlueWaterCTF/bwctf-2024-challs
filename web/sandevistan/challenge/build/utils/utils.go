package utils

import (
	"Sandevistan/models"
	"net/http"
	"html/template"
	"regexp"
	"os"
	"path/filepath"
	"fmt"
	"context"
)

var validPath = regexp.MustCompile("^/tmpl/([a-zA-Z0-9]+)$")

func GetCwd() string {
	cwd, _ := os.Getwd()
	return cwd
}

func renderError(w http.ResponseWriter) {
	errpath := filepath.Join(GetCwd(), "tmpl", "error.html")
	errTemplate, _ := template.ParseFiles(errpath)
	errTemplate.Execute(w, nil)
}

func RenderTemplate[S any](w http.ResponseWriter, tmpl string, s S) {
	m := validPath.FindStringSubmatch(tmpl)
    if m == nil {
		fmt.Println("string match error")
		renderError(w)
		return
    }
	htmlTmpl := m[0] + ".html"
	fpath := filepath.Join(GetCwd(), htmlTmpl)
	t, err := template.ParseFiles(fpath)
	if err != nil {
		fmt.Println(err)
		renderError(w)
		return
	}
    t.Execute(w, s)
}


func AlphaNumCheck(ctx context.Context, t string) *models.UserError {
	if !regexp.MustCompile(`^[a-zA-Z0-9]*$`).MatchString(t) {
		v := fmt.Sprintf("ERROR! Invalid Value: %s\n", t)
		username := ctx.Value("username")
		regexErr := ErrorFactory(ctx, v, username.(string))
		return regexErr
	}
	return nil
}

func ErrorFactory(ctx context.Context, v string, f string) *models.UserError {
	filename := "errorlog/" + f
	UErr := &models.UserError{
		v,
		f,
		ctx,
	}
	file, _ := os.OpenFile(filename, os.O_RDWR|os.O_CREATE, 0644)
	defer file.Close()

	file.WriteString(v)
	return UErr
}