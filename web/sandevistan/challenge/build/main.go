package main

import (
	"Sandevistan/server"
	"log"
	//"os"
)

func main() {
	s := server.NewServer()
	log.Fatal(s.Serve())
}
