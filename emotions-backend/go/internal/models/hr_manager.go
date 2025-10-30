package models

type HRManager struct {
	IDHRManager int    `json:"id_hr_manager"`
	FullName    string `json:"full_name"`
	Email       string `json:"email"`
}
