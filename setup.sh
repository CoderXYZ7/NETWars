#!/bin/bash

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run with sudo privileges. Please run with sudo."
    exit 1
fi

# Function to detect the package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    elif command -v brew &> /dev/null; then
        echo "brew"
    elif command -v port &> /dev/null; then
        echo "port"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos-no-pm"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install a package using the detected package manager
install_package() {
    local package_name=$1
    local pkg_manager=$(detect_package_manager)

    echo "Detected package manager: $pkg_manager"

    case $pkg_manager in
        apt)
            apt-get update
            apt-get install -y "$package_name"
            ;;
        dnf)
            dnf install -y "$package_name"
            ;;
        yum)
            yum install -y "$package_name"
            ;;
        pacman)
            pacman -Sy --noconfirm "$package_name"
            ;;
        zypper)
            zypper install -y "$package_name"
            ;;
        brew)
            # Homebrew shouldn't be run as root
            if [ "$EUID" -eq 0 ]; then
                echo "Warning: Running Homebrew as root is not recommended."
                echo "Please run the script without sudo for Homebrew installations."
                return 1
            fi
            brew install "$package_name"
            ;;
        port)
            port install "$package_name"
            ;;
        macos-no-pm)
            echo "No package manager found on macOS. Installing Homebrew..."
            if [ "$EUID" -eq 0 ]; then
                echo "Warning: Installing Homebrew as root is not recommended."
                echo "Please run the script without sudo for Homebrew installation."
                return 1
            fi
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install "$package_name"
            ;;
        windows)
            echo "On Windows systems, please use WSL or install $package_name manually."
            return 1
            ;;
        unknown)
            echo "Unknown system or package manager. Please install $package_name manually."
            return 1
            ;;
    esac

    return $?
}

# Check if git is installed, install if needed
echo "Checking for Git..."
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing Git..."
    install_package "git"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install Git. Please install it manually."
        exit 1
    fi
    echo "Git installed successfully."
else
    echo "Git is already installed."
fi

# Clone the project from GitHub
echo "Cloning the repository..."
if [ -d "NETWars" ]; then
    echo "NETWars directory already exists. Pulling latest changes..."
    cd NETWars
    git pull
    cd ..
else
    git clone https://github.com/CoderXYZ7/NETWars.git
    if [ $? -ne 0 ]; then
        echo "Error: Failed to clone the repository."
        exit 1
    fi
fi

# Check if Python is installed, install if needed
echo "Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python not found. Installing Python..."
    pkg_manager=$(detect_package_manager)

    case $pkg_manager in
        apt)
            install_package "python3"
            install_package "python3-venv"
            install_package "python3-pip"
            ;;
        dnf|yum)
            install_package "python3"
            install_package "python3-venv"
            install_package "python3-pip"
            ;;
        pacman)
            install_package "python"
            install_package "python-pip"
            ;;
        zypper)
            install_package "python3"
            install_package "python3-venv"
            install_package "python3-pip"
            ;;
        brew)
            install_package "python"
            ;;
        port)
            install_package "python311"  # Adjust version as needed
            ;;
        *)
            echo "Error: Unsupported package manager for Python installation. Please install Python manually."
            exit 1
            ;;
    esac

    echo "Python installed successfully."
else
    echo "Python is already installed."
fi

# Check if pip is installed, install if needed
echo "Checking for pip..."
if ! command -v pip3 &> /dev/null; then
    echo "Pip not found. Installing pip..."
    pkg_manager=$(detect_package_manager)

    case $pkg_manager in
        apt|dnf|yum|zypper)
            install_package "python3-pip"
            ;;
        pacman)
            # Python comes with pip on Arch
            echo "Pip should already be installed with Python on Arch-based systems."
            ;;
        brew|port)
            # pip should be installed with Python via brew/port
            echo "Pip should have been installed with Python, but it's not found. Trying to install pip..."
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py
            rm get-pip.py
            ;;
        *)
            echo "Error: Unsupported package manager for pip installation. Please install pip manually."
            exit 1
            ;;
    esac

    echo "Pip installed successfully."
else
    echo "Pip is already installed."
fi

# Check for python-venv package on systems that separate it
if ! python3 -m venv --help &> /dev/null; then
    echo "Python venv module not found. Installing python-venv..."
    pkg_manager=$(detect_package_manager)

    case $pkg_manager in
        apt|dnf|yum|zypper)
            install_package "python3-venv"
            ;;
        # Other package managers typically include venv with Python
    esac
fi

# Navigate to project directory
echo "Navigating to project directory..."
cd NETWars || { echo "Error: NETWars directory not found."; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# Install requirements
echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements."
        exit 1
    fi
else
    echo "Warning: requirements.txt not found."
fi


# Start both bk/server.sh and Launcher.py
echo "Starting Launcher.py..."

# Check if both files exist
if [ -f "Launcher.py" ]; then
    # Start Launcher.py in the foreground
    echo "Starting Launcher.py in the foreground..."
    python Launcher.py
else
    echo "Error: Launcher.py not found."
    exit 1
fi

echo "Setup complete!"
