package models

type Feature struct {
	IDFeature      int    `json:"id_feature"`
	IDSession      int    `json:"id_session"`
	FacialFeatures string `json:"facial_features"` // JSON
	MFCC           string `json:"mfcc"`            // JSON
}
