package main

import (
	"net/http"
	"path/filepath"
	"strconv"

	"github.com/gorilla/mux"
)

// Sector describes an industry sector in an input-output model.
type Sector struct {
	ID          string `json:"id"`
	Index       int    `json:"index"`
	Name        string `json:"name"`
	Code        string `json:"code"`
	Location    string `json:"location"`
	Description string `json:"description"`
}

// ReadSectors reads the sectors from the CSV file in the data folder. It
// returns them in a slice where the sectors are sorted by their indices.
func ReadSectors(folder string) ([]*Sector, error) {
	path := filepath.Join(folder, "sectors.csv")
	records, err := ReadCSV(path)
	if err != nil {
		return nil, err
	}

	sectors := make([]*Sector, len(records)-1)
	for idx, row := range records {
		if idx == 0 {
			continue
		}
		s := Sector{}
		s.Index, err = strconv.Atoi(row[0])
		if err != nil {
			return nil, err
		}
		s.ID = row[1]
		s.Name = row[2]
		s.Code = row[3]
		s.Location = row[4]
		s.Description = row[5]
		sectors[s.Index] = &s
	}
	return sectors, nil
}

// HandleGetSectors returns the handler for GET /api/{model}/sectors
func HandleGetSectors(dataDir string) http.HandlerFunc {

	return func(w http.ResponseWriter, r *http.Request) {
		model := mux.Vars(r)["model"]
		folder := filepath.Join(dataDir, model)
		sectors, err := ReadSectors(folder)
		if err != nil {
			http.Error(w, "no sectors for model "+model+" found",
				http.StatusNotFound)
			return
		}
		ServeJSON(sectors, w)
	}
}

// HandleGetSector returns the handler for GET /api/{model}/sectors/{id}
func HandleGetSector(dataDir string) http.HandlerFunc {

	return func(w http.ResponseWriter, r *http.Request) {
		model := mux.Vars(r)["model"]
		id := mux.Vars(r)["id"]
		folder := filepath.Join(dataDir, model)
		sectors, err := ReadSectors(folder)
		if err != nil {
			http.Error(w, "no sectors for model "+model+" found",
				http.StatusNotFound)
			return
		}
		for i := range sectors {
			s := sectors[i]
			if s.ID == id {
				ServeJSON(s, w)
				return
			}
		}
		http.Error(w, "no sector with id "+id+" for model "+model+" found",
			http.StatusNotFound)
	}
}
