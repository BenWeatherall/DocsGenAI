#!/bin/bash

set -e  # Exit on any error

GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m' # No Color


printf "\n${GREEN}Starting installation process...${NC}\n"

# uv venv --python 3.12 will provision/fetch the interpreter (no system Python check needed)

# Clean Python cache files
printf "\n${GREEN}Cleaning Python cache files...${NC}\n"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
rm -rf .venv 2>/dev/null || true
rm -rf dist 2>/dev/null || true
printf "\n${GREEN}Cache cleanup complete${NC}\n"

# Installing UV
printf "\n${GREEN}Checking UV installation...${NC}\n"
if ! command -v uv &> /dev/null; then
  printf "\n${GREEN}Installing UV via official installer...${NC}\n"
  curl -LsSf https://astral.sh/uv/install.sh | sh || { printf "\n${RED}Failed to install UV${NC}\n"; exit 1; }
  export PATH="$HOME/.local/bin:$PATH"
  if ! command -v uv &> /dev/null; then
    printf "\n${RED}UV installed but not on PATH. Add \$HOME/.local/bin to PATH and re-run.${NC}\n"
    exit 1
  fi
else
  printf "\n${GREEN}UV is already installed${NC}\n"
fi

# Create and activate virtual environment
printf "\n${GREEN}Creating virtual environment...${NC}\n"
uv venv --python 3.12 || { printf "\n${RED}Failed to create virtual environment${NC}\n"; exit 1; }
source .venv/bin/activate || { printf "\n${RED}Failed to activate virtual environment${NC}\n"; exit 1; }

# Verify virtual environment activation
if [[ -z "$VIRTUAL_ENV" ]]; then
    printf "\n${RED}Virtual environment activation failed${NC}\n"
    exit 1
fi

# Install keyring
printf "\n${GREEN}Installing keyring...${NC}\n"
uv pip install keyrings.google-artifactregistry-auth --no-config || { printf "\n${RED}Failed to install keyring${NC}\n"; exit 1; }

# Install project
printf "\n${GREEN}Installing project dependencies...${NC}\n"
uv pip install -e ".[dev]" \
    --upgrade \
    --no-cache-dir || { printf "\n${RED}Failed to install project dependencies${NC}\n"; exit 1; }

# Run tests
printf "\n${GREEN}Running tests...${NC}\n"
pytest || { printf "\n${RED}Tests failed${NC}\n"; exit 1; }

printf "\n${GREEN}Installation completed successfully!${NC}\n"
