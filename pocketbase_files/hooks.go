package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/pocketbase/pocketbase/core"
)

type GenerateFlashcardsJobTriggerPayload struct {
	GenerateFlashcardJobId string `json:"generate_flashcards_job_id"`
}

func registerJobRequestsHook(app core.App) {
	app.OnRecordAfterCreateSuccess("job_requests").BindFunc(func(e *core.RecordEvent) error {
		log.Printf("Hook triggered for 'job_requests' collection: Record ID = %s\n", e.Record.Id)

		go func(recId string) {
			payload := GenerateFlashcardsJobTriggerPayload{
				GenerateFlashcardJobId: recId,
			}

			payloadBytes, err := json.Marshal(payload)
			if err != nil {
				log.Printf("Error marshalling payload for record ID %s: %v", recId, err)
				return
			}

			apiServerBaseURL := os.Getenv("INTERNAL_API_URL")
			resp, err := http.Post(apiServerBaseURL+"/generate-flashcards-job", "application/json", bytes.NewBuffer(payloadBytes))

			if err != nil {
				log.Printf("Error calling generate-flashcards for record ID %s: %v", recId, err)
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode == http.StatusAccepted || resp.StatusCode == http.StatusOK {
				log.Printf("Successfully triggered generate-flashcards via Flask for record ID %s", recId)
			} else {
				log.Printf("Failed to trigger generate-flashcards for record ID %s via Flask. Status: %s", recId, resp.Status)
			}
		}(e.Record.Id)

		return e.Next()
	})
}
