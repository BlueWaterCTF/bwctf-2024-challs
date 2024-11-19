package models

import (
	"os/exec"
	"errors"
)

type CyberWare struct {
	Name			string
	BaseQuality		int
	Capacity		int
	Iconic			bool
	Username		string
}

func (u *User) CyberHealthcheck() ([]byte, error) {
	cmd := exec.Command("/bin/true")	
	output, err := cmd.CombinedOutput()
    if err != nil {
		return nil, errors.New("error in healthcheck")
        panic(err)
    }
	return output, nil
}
