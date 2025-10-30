package models

type Emotion struct {
	IDEmotion   int     `json:"id_emotion"`
	IDSession   int     `json:"id_session"`
	Emotion     string  `json:"emotion"`
	Probability float64 `json:"probability"`
}
