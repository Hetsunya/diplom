package models

type Report struct {
	IDReport    int    `json:"id_report"`
	IDSession   int    `json:"id_session"`
	IDHRManager int    `json:"id_hr_manager"`
	Metrics     string `json:"metrics"`
	Summary     string `json:"summary"`
}
