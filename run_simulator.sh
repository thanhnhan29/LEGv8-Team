#!/bin/bash

echo "===================================="
echo "LEGv8 Simulator Setup and Run Script"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}Python is already installed: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ $PYTHON_VERSION == 3.* ]]; then
        echo -e "${GREEN}Python is already installed: $PYTHON_VERSION${NC}"
        PYTHON_CMD="python"
    else
        echo -e "${RED}Python 2 detected. Python 3 is required.${NC}"
        INSTALL_PYTHON=true
    fi
else
    echo -e "${YELLOW}Python is not installed. Installing Python 3.9...${NC}"
    INSTALL_PYTHON=true
fi

# Install Python if needed
if [ "$INSTALL_PYTHON" = true ]; then
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Detected Linux system"
        if command_exists apt-get; then
            # Ubuntu/Debian
            echo "Installing Python 3.9 via apt..."
            sudo apt-get update
            sudo apt-get install -y python3.9 python3.9-pip python3.9-venv
            PYTHON_CMD="python3.9"
        elif command_exists yum; then
            # CentOS/RHEL
            echo "Installing Python 3.9 via yum..."
            sudo yum install -y python39 python39-pip
            PYTHON_CMD="python3.9"
        elif command_exists dnf; then
            # Fedora
            echo "Installing Python 3.9 via dnf..."
            sudo dnf install -y python3.9 python3-pip
            PYTHON_CMD="python3.9"
        else
            echo -e "${RED}Could not detect package manager. Please install Python 3.9 manually.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "Detected macOS system"
        if command_exists brew; then
            echo "Installing Python 3.9 via Homebrew..."
            brew install python@3.9
            PYTHON_CMD="python3.9"
        else
            echo -e "${YELLOW}Homebrew not found. Installing Homebrew first...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python@3.9
            PYTHON_CMD="python3.9"
        fi
    else
        echo -e "${RED}Unsupported operating system. Please install Python 3.9 manually.${NC}"
        exit 1
    fi
fi

# Verify Python installation
if ! command_exists $PYTHON_CMD; then
    echo -e "${RED}Python installation failed. Please install Python 3.9 manually.${NC}"
    exit 1
fi

# Check if pip is available
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo -e "${YELLOW}Pip not found. Installing pip...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $PYTHON_CMD get-pip.py
    rm get-pip.py
    PIP_CMD="pip"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    cat > requirements.txt << EOF
Flask==2.3.3
flask-cors==4.0.0
EOF
fi

# Install dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
$PIP_CMD install -r requirements.txt

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
fi

# Make sure we're in the correct directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Please run this script from the LEGv8-Team directory.${NC}"
    exit 1
fi

# Start the simulator
echo ""
echo "===================================="
echo -e "${GREEN}Starting LEGv8 Simulator...${NC}"
echo "===================================="
echo ""
echo -e "${YELLOW}The simulator will be available at: http://localhost:5010${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the simulator${NC}"
echo ""

# Run the simulator
$PYTHON_CMD app.py