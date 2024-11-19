package models

import (
	"context"
	"os"
	"errors"
	"os/exec"
)

type UserError struct {
	Value		string
	Filename	string
	Ctx			context.Context
}

type User struct {
	Name			string
	Augments		map[string]CyberWare
	Errors			[]*UserError
}

func (u *User) AllCyberWares() map[string]CyberWare {
	return u.Augments
}

func (u *User) AddCyberWare(cw CyberWare) {
	u.Augments[cw.Name] = cw
}

func (u *User) AddError(ue *UserError) {
	u.Errors = append(u.Errors, ue)
}

func (u *User) NewError(val string, fname string) *UserError {
	ctx := context.Background()
	ue := &UserError{
		Value: val,
		Filename: fname,
		Ctx: ctx,
	}
	u.Errors = append(u.Errors, ue)
	return ue
}

func (u *User) SerializeErrors(data string, index int, offset int64) error {
 	fname := u.Errors[index]

	if fname == nil {
		return errors.New("Error not found")
	}
 
	f, err := os.OpenFile(fname.Filename, os.O_RDWR, 0)
	if err != nil {
		return errors.New("File not found")
	}
	defer f.Close()

	_, ferr := f.WriteAt([]byte(data), offset)
	if ferr != nil {
		return errors.New("File error writing")
	}

	return nil
}

func (u *User) UserHealthcheck() ([]byte, error) {
	cmd := exec.Command("/bin/true")	
	output, err := cmd.CombinedOutput()
    if err != nil {
		return nil, errors.New("error in healthcheck")
        panic(err)
    }
	return output, nil
}
