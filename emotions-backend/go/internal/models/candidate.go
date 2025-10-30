package models

type Candidate struct {
	IDCandidate int    `json:"id_candidate"`
	FullName    string `json:"full_name"`
	Position    string `json:"position"`
}
