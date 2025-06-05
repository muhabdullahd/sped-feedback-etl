#!/bin/zsh
# Setup script for Special Education Feedback Insight System
# This script:
# - Creates a Python virtual environment
# - Installs dependencies
# - Launches MySQL, RabbitMQ, and the Flask application
# - Optionally starts the Airflow webserver

set -e  # Exit on error

# Terminal colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print section header
print_header() {
    echo ""
    echo "${BLUE}============================================================${NC}"
    echo "${BLUE}  $1${NC}"
    echo "${BLUE}============================================================${NC}"
    echo ""
}

# Print success message
print_success() {
    echo "${GREEN}✓ $1${NC}"
}

# Print info message
print_info() {
    echo "${YELLOW}➜ $1${NC}"
}

# Print error message
print_error() {
    echo "${RED}✗ $1${NC}"
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

print_header "Setting up Special Education Feedback Insight System"

# Check for Python 3.8+
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.8 or newer."
    exit 1
fi

PY_VERSION=$(python3 --version | cut -d' ' -f2)
PY_MAJOR=$(echo "$PY_VERSION" | cut -d'.' -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d'.' -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
    print_error "Python 3.8+ is required. Found: Python $PY_VERSION"
    exit 1
fi

print_success "Found Python $PY_VERSION"

# Create virtual environment
print_info "Creating virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
print_header "Installing Dependencies"
print_info "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Check platform for macOS-specific installation
if [[ $(uname) == "Darwin" ]]; then
    print_info "Detected macOS, using enhanced installation approach..."
    
    # Install core packages with special handling to avoid compilation issues
    print_info "Installing core packages with special handling..."
    pip install --upgrade numpy pandas scipy scikit-learn --no-build-isolation
    
    # Install packages that might have Windows dependencies with binary preference
    print_info "Installing packages with platform-specific handling..."
    pip install --only-binary :all: cryptography
    
    # Try to install remaining packages
    print_info "Installing remaining packages from requirements.txt..."
    # Use grep to filter out already installed packages
    grep -v -E "numpy|pandas|scipy|scikit-learn|cryptography" requirements.txt > temp_requirements.txt
    pip install -v -r temp_requirements.txt || {
        print_error "Some packages failed to install. Trying individual installation..."
        # If batch install fails, try one by one
        while read -r package; do
            if [[ ! -z "$package" && "$package" != \#* ]]; then
                print_info "Installing $package..."
                pip install "$package" || print_error "Failed to install $package, continuing..."
            fi
        done < requirements.txt
    }
    rm -f temp_requirements.txt
else
    # For non-macOS platforms, use standard installation
    print_info "Installing Python packages from requirements.txt..."
    pip install -v -r requirements.txt
fi

print_success "Dependencies installed"

# Create logs directory
mkdir -p logs
print_success "Created logs directory"

# Setup MySQL
print_header "Setting up MySQL"
MYSQL_DB_CREATED=false # Flag to track if DB setup was successful

if ! command -v mysql &> /dev/null; then
    print_info "MySQL command-line tool not found."
    if command -v brew &> /dev/null; then
        print_info "Attempting to install MySQL with Homebrew..."
        brew install mysql
        if ! command -v mysql &> /dev/null; then
            print_error "MySQL installation via Homebrew failed or 'mysql' is still not in PATH."
            print_info "Please install MySQL manually and ensure 'mysql' is in your PATH."
        else
            print_success "MySQL installed via Homebrew."
        fi
    else
        print_error "Homebrew not found. Please install MySQL manually or install Homebrew first."
    fi
fi

if command -v mysql &> /dev/null; then
    print_info "Attempting to start MySQL service (if not already running)..."
    if brew services list | grep -q "mysql.*started"; then
        print_info "MySQL service is already running."
    else
        brew services start mysql || print_warning "Could not start MySQL service with 'brew services start mysql'. It might be managed differently or have issues."
        # Give it a moment to start
        sleep 3
        if ! brew services list | grep -q "mysql.*started"; then
             # Attempt to ping server to see if it's up
             if ! mysqladmin ping -u root --silent &>/dev/null && ! mysqladmin ping -u root -p --silent &>/dev/null; then # Try with and without password prompt
                print_error "MySQL service does not seem to be running after attempting to start."
                print_info "Please ensure MySQL server is running before proceeding."
             else
                print_info "MySQL server is responding."
             fi
        fi
    fi

    print_info "Attempting to create/verify the 'sped_feedback' database..."
    # Try without a password first (common for fresh Homebrew installs)
    if mysql -u root -e "CREATE DATABASE IF NOT EXISTS sped_feedback;" &>/dev/null; then
        print_success "Database 'sped_feedback' created/verified successfully (MySQL root has no password or access granted)."
        MYSQL_DB_CREATED=true
    else
        print_info "Accessing MySQL as 'root' without a password failed."
        print_info "This usually means the MySQL 'root' user has a password set."
        print_info "Please enter your MySQL 'root' user password (it will not be shown as you type):"
        read -s MYSQL_PASSWORD # Read password silently

        if [ -z "$MYSQL_PASSWORD" ]; then
            print_warning "No password entered. If 'root' has a password, this will likely fail."
            # Attempt will be made with an empty password string if user just hits enter
        fi

        # Try with the provided password
        if mysql -u root -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS sped_feedback;" &>/dev/null; then
            print_success "Database 'sped_feedback' created/verified successfully using the provided password."
            MYSQL_DB_CREATED=true

            print_info "Would you like to try updating 'flask_app/config.py' with this MySQL password? (y/n)"
            read -r update_config
             if [[ "$update_config" =~ ^[Yy]$ ]]; then
                 if [ -f "flask_app/config.py" ]; then # Added 'then' here
                     # Backup config
                     cp flask_app/config.py flask_app/config.py.bak
                     print_info "Backed up 'flask_app/config.py' to 'flask_app/config.py.bak'"
                     # Update config - BE CAREFUL with sed, this is a basic attempt
                     # This regex assumes a specific format like mysql://root:PASSWORD@...
                     # It might need adjustment for other formats (e.g., pymysql)
                     if sed -i '' "s|\(mysql\(+pymysql\)\?://root:\)[^@]*@|\1$MYSQL_PASSWORD@|g" flask_app/config.py; then
                         print_success "Attempted to update database password in 'flask_app/config.py'."
                         print_info "Please verify the change in 'flask_app/config.py' is correct."
                     else 
                         print_error "Failed to automatically update 'flask_app/config.py'."
                         print_info "Please manually update the MySQL password in 'flask_app/config.py'."
                     fi 
                 else 
                     print_info "'flask_app/config.py' not found. Please manually update your application's MySQL configuration if needed."
                 fi
             fi
            # This block is reached if creating DB with prompted password failed
            print_error "MySQL access failed. The password entered for 'root' may be incorrect, or root access is misconfigured."
            print_error "To resolve this, you MUST MANUALLY RESET the MySQL 'root' user password."
            print_info "--------------------------------------------------------------------------------"
            print_info "Steps to reset MySQL root password on macOS (using Homebrew):"
            print_info "1. Stop MySQL service: ${YELLOW}brew services stop mysql${NC}"
            
            MYSQL_PREFIX=$(brew --prefix mysql 2>/dev/null || echo "/opt/homebrew/opt/mysql") # Default if brew --prefix fails
            MYSQLD_SAFE_PATH="$MYSQL_PREFIX/bin/mysqld_safe"
            if [ ! -f "$MYSQLD_SAFE_PATH" ]; then 
                MYSQL_PREFIX_INTEL="/usr/local/opt/mysql" # Fallback for older Intel paths
                if [ -f "$MYSQL_PREFIX_INTEL/bin/mysqld_safe" ]; then
                    MYSQLD_SAFE_PATH="$MYSQL_PREFIX_INTEL/bin/mysqld_safe"
                    MYSQL_PREFIX=$MYSQL_PREFIX_INTEL
                else
                     print_warning "Could not reliably determine mysqld_safe path. Assuming default: $MYSQLD_SAFE_PATH"
                fi
            fi

            print_info "2. Start MySQL in safe mode (bypasses password checks):"
            print_info "   Command: ${YELLOW}sudo $MYSQLD_SAFE_PATH --skip-grant-tables --skip-networking &${NC}"
            print_info "   (After running, wait a few seconds. Press Enter if your prompt doesn't return immediately.)"
            print_info "   (If it prints 'mysqld from pid file ... ended' and stops, this method might be failing. Try Method B below.)"
            print_info "3. Connect to MySQL (no password needed now): ${YELLOW}mysql -u root${NC}"
            print_info "4. In the MySQL prompt, run these SQL commands (replace 'YourNewSecurePassword' with your actual new password):"
            print_info "   ${YELLOW}FLUSH PRIVILEGES;${NC}"
            print_info "   ${YELLOW}ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewSecurePassword';${NC}"
            print_info "   ${YELLOW}FLUSH PRIVILEGES;${NC}"
            print_info "   ${YELLOW}EXIT;${NC}"
            print_info "5. Stop the safe-mode MySQL server (important!):"
            print_info "   Command: ${YELLOW}sudo killall mysqld mysqld_safe mysqld_safe_helper 2>/dev/null || echo 'No manual mysqld processes found to kill.'${NC}"
            print_info "6. Start MySQL service normally: ${YELLOW}brew services start mysql${NC}"
            print_info "7. Test your new password: ${YELLOW}mysql -u root -p${NC} (enter 'YourNewSecurePassword')"
            print_info "--------------------------------------------------------------------------------"
            print_info "${RED}Alternative Reset Method (if --skip-grant-tables fails, for MySQL 8+):${NC}"
            print_info "1. Ensure MySQL is stopped: ${YELLOW}brew services stop mysql${NC}"
            print_info "2. Create a temporary file named ${GREEN}mysql-reset.sql${NC} in your current directory (${YELLOW}$(pwd)${NC}) with ONLY this line:"
            print_info "   ${YELLOW}ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewSecurePassword';${NC}"
            print_info "3. Start MySQL with this init-file (as the _mysql user):"
            print_info "   Command: ${YELLOW}sudo $MYSQLD_SAFE_PATH --init-file=$(pwd)/mysql-reset.sql --user=_mysql &${NC}"
            print_info "   (MySQL should start, apply the password change, and then stop. Check logs in ${YELLOW}${MYSQL_PREFIX}/var/mysql/$(hostname).err${NC})"
            print_info "4. Clean up (after MySQL has processed the init-file and stopped):"
            print_info "   Command: ${YELLOW}sudo killall mysqld mysqld_safe mysqld_safe_helper 2>/dev/null; rm mysql-reset.sql${NC}"
            print_info "5. Start MySQL normally: ${YELLOW}brew services start mysql${NC}"
            print_info "6. Test login with 'YourNewSecurePassword': ${YELLOW}mysql -u root -p${NC}"
            print_info "--------------------------------------------------------------------------------"
            print_info "After successfully resetting the password, re-run this setup script. Enter the new password when prompted."
        fi
    fi

    if [ "$MYSQL_DB_CREATED" = true ]; then
        print_success "MySQL database 'sped_feedback' is configured."
    else
        print_error "MySQL setup FAILED due to password/access issues. Please follow the reset instructions above."
    fi
else
    print_error "MySQL command-line tool ('mysql') not found. Cannot proceed with MySQL setup."
    print_info "Please install MySQL and ensure it's in your PATH, or configure your application to use a different database."
fi

# Setup RabbitMQ
# ... (rest of the script) ...





# Start RabbitMQ if installed
if command -v rabbitmq-server &> /dev/null; then
    print_info "Starting RabbitMQ service..."
    brew services start rabbitmq || print_error "Failed to start RabbitMQ. It may already be running."
    print_success "RabbitMQ setup completed"
else
    print_info "RabbitMQ not available. Please install manually or update celery_tasks/celery.py with your broker settings."
fi

# Find the Airflow section (around line 255) and replace it with this:

# Ask if user wants to start Airflow
print_header "Airflow Setup (Optional)"
print_info "Do you want to initialize and start Airflow? (y/n)"
read -r start_airflow

if [[ "$start_airflow" =~ ^[Yy]$ ]]; then
    print_info "Setting up Airflow..."
    
    # Fix markupsafe compatibility issue
    print_info "Installing compatible markupsafe version for Airflow..."
    pip install markupsafe==2.0.1
    
    # Set Airflow home
    export AIRFLOW_HOME="$PROJECT_ROOT/airflow"
    mkdir -p "$AIRFLOW_HOME"
    
    # Initialize Airflow database
    print_info "Initializing Airflow database..."
    # First completely remove any existing Airflow data to ensure clean initialization
    if [ -d "$AIRFLOW_HOME" ]; then
        print_info "Removing existing Airflow directory to ensure clean initialization..."
        rm -rf "$AIRFLOW_HOME"
        mkdir -p "$AIRFLOW_HOME"
    fi

    # Initialize Airflow database
    export AIRFLOW_HOME="$PROJECT_ROOT/airflow"
    print_info "Running airflow db init..."
    airflow db init
    
    # Create Airflow user if none exists
    print_info "Creating Airflow admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin || print_info "User may already exist, continuing..."
    
    # Set Airflow to use our DAGs
    mkdir -p "$AIRFLOW_HOME/dags"
    print_info "Linking Airflow DAGs..."
    for dag_file in "$PROJECT_ROOT/airflow_dags"/*.py; do
        if [ -f "$dag_file" ] && [[ "$dag_file" != *"__init__.py" ]]; then
            ln -sf "$dag_file" "$AIRFLOW_HOME/dags/$(basename "$dag_file")" || print_error "Failed to link $dag_file"
        fi
    done
    
    # Start Airflow in the background
    print_info "Starting Airflow webserver in the background..."
    airflow webserver -p 8080 > logs/airflow_webserver.log 2>&1 &
    AIRFLOW_WEBSERVER_PID=$!
    print_success "Airflow webserver started with PID: $AIRFLOW_WEBSERVER_PID"
    
    print_info "Starting Airflow scheduler in the background..."
    airflow scheduler > logs/airflow_scheduler.log 2>&1 &
    AIRFLOW_SCHEDULER_PID=$!
    print_success "Airflow scheduler started with PID: $AIRFLOW_SCHEDULER_PID"
    
    print_success "Airflow is now running at http://localhost:8080"
    print_info "Username: admin, Password: admin"
else
    print_info "Skipping Airflow setup. You can start it later with:"
    print_info "export AIRFLOW_HOME=\"$PROJECT_ROOT/airflow\""
    print_info "airflow webserver -p 8080"
    print_info "airflow scheduler"
fi

# Start Flask app
print_header "Starting Flask Application"
print_info "Do you want to start the Flask application? (y/n)"
read -r start_flask

if [[ "$start_flask" =~ ^[Yy]$ ]]; then
    print_info "Starting Flask application in the background..."
    export FLASK_APP=flask_app.app
    export FLASK_ENV=development
    flask run --host=0.0.0.0 --port=5000 > logs/flask.log 2>&1 &
    FLASK_PID=$!
    print_success "Flask application started with PID: $FLASK_PID"
    print_success "Flask app is now running at http://localhost:5000"
else
    print_info "Skipping Flask application. You can start it later with:"
    print_info "export FLASK_APP=flask_app.app"
    print_info "export FLASK_ENV=development"
    print_info "flask run --host=0.0.0.0 --port=5000"
fi

# Start Celery worker
print_header "Starting Celery Worker"
print_info "Do you want to start the Celery worker? (y/n)"
read -r start_celery

if [[ "$start_celery" =~ ^[Yy]$ ]]; then
    print_info "Starting Celery worker in the background..."
    python -m celery_tasks.worker > logs/celery.log 2>&1 &
    CELERY_PID=$!
    print_success "Celery worker started with PID: $CELERY_PID"
else
    print_info "Skipping Celery worker. You can start it later with:"
    print_info "python -m celery_tasks.worker"
fi

# Start Streamlit dashboard
print_header "Starting Streamlit Dashboard"
print_info "Do you want to start the Streamlit dashboard? (y/n)"
read -r start_streamlit

if [[ "$start_streamlit" =~ ^[Yy]$ ]]; then
    print_info "Starting Streamlit dashboard in the background..."
    streamlit run dashboard/streamlit_app.py > logs/streamlit.log 2>&1 &
    STREAMLIT_PID=$!
    print_success "Streamlit dashboard started with PID: $STREAMLIT_PID"
    print_success "Streamlit dashboard is now running at http://localhost:8501"
else
    print_info "Skipping Streamlit dashboard. You can start it later with:"
    print_info "streamlit run dashboard/streamlit_app.py"
fi

print_header "Setup Complete"
print_success "Special Education Feedback Insight System is ready!"
print_info "Services running in the background:"

[ -n "$FLASK_PID" ] && print_info "- Flask app (PID: $FLASK_PID): http://localhost:5000"
[ -n "$CELERY_PID" ] && print_info "- Celery worker (PID: $CELERY_PID)"
[ -n "$AIRFLOW_WEBSERVER_PID" ] && print_info "- Airflow webserver (PID: $AIRFLOW_WEBSERVER_PID): http://localhost:8080"
[ -n "$AIRFLOW_SCHEDULER_PID" ] && print_info "- Airflow scheduler (PID: $AIRFLOW_SCHEDULER_PID)"
[ -n "$STREAMLIT_PID" ] && print_info "- Streamlit dashboard (PID: $STREAMLIT_PID): http://localhost:8501"

print_info "Check the logs directory for service output."
print_info "To deactivate the virtual environment when done, run: deactivate"