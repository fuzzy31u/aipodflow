#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test health endpoint
echo -e "${GREEN}Testing health endpoint...${NC}"
curl -s http://localhost:8080/health
echo -e "\n"

# Test process endpoint with a test audio file
echo -e "${GREEN}Testing process endpoint...${NC}"
# Create a simple test file
echo "This is a test file" > test/data/test.txt

# Upload the test file
echo -e "${GREEN}Uploading test file...${NC}"
curl -X POST -F "audio=@test/data/test.txt" http://localhost:8080/api/v1/process
echo -e "\n" 