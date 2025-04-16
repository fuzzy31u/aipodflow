.PHONY: build run test clean cli docker-build docker-run

# Build the application
build:
	go build -o bin/mcp .

cli:
	mkdir -p bin
	go build -o bin/podcast-cli ./cmd/podcast-cli

# Run the application
run:
	go run main.go

# Run tests
test:
	go test ./...

# Clean build artifacts
clean:
	rm -f mcp
	rm -rf uploads/*

# Build Docker image
docker-build:
	docker build -t mcp .

# Run Docker container
docker-run:
	docker-compose up -d

# Stop Docker container
docker-stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f 