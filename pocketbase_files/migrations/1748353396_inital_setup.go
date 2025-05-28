package migrations

import (
	"os"

	"github.com/pocketbase/pocketbase/core"
	m "github.com/pocketbase/pocketbase/migrations"
)

func init() {
	m.Register(func(app core.App) error {
		superusers, err := app.FindCollectionByNameOrId(core.CollectionNameSuperusers)
		if err != nil {
			return err
		}

		superuserEmail := os.Getenv("INITIAL_ADMIN_EMAIL")
		superuserPassword := os.Getenv("INITIAL_ADMIN_PASSWORD")
		adminRecord := core.NewRecord(superusers)
		adminRecord.Set("email", superuserEmail)
		adminRecord.Set("password", superuserPassword)
		app.Save(adminRecord)

		temporalBotEmail := os.Getenv("TEMPORAL_BOT_EMAIL")
		temporalBotPassword := os.Getenv("TEMPORAL_BOT_PASSWORD")
		temporalBotRecord := core.NewRecord(superusers)
		temporalBotRecord.Set("email", temporalBotEmail)
		temporalBotRecord.Set("password", temporalBotPassword)
		return app.Save(temporalBotRecord)

	}, func(app core.App) error {
		// Area for reverting changes, for superuser setup - not needed
		return nil
	})
}
