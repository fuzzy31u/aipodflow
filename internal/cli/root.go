package cli

import (
	"github.com/spf13/cobra"
)

// NewRootCmd はルートコマンドを作成する
func NewRootCmd() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "podcast-cli",
		Short: "Podcast automation tool",
		Long:  `A CLI tool for automating podcast production workflow with interactive content selection.`,
	}

	// サブコマンドを追加
	rootCmd.AddCommand(NewProcessCmd())
	
	return rootCmd
}
