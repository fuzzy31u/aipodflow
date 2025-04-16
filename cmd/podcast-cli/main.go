package main

import (
	"fmt"
	"os"

	"github.com/automate-podcast/internal/cli"
)

func main() {
	// ルートコマンドの作成と実行
	rootCmd := cli.NewRootCmd()
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
