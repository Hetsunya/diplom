package models

import "time"

type Session struct {
	IDSession   int       `json:"id_session"`
	IDCandidate int       `json:"id_candidate"`
	IDHRManager int       `json:"id_hr_manager"`
	DateTime    time.Time `json:"date_time"`
	Video       string    `json:"video"`
	Audio       string    `json:"audio"`
}
