#!/bin/zsh
# filepath: /Users/muhammad/Downloads/sped-feedback-etl/install_deps.sh

# Enhanced dependency installation script for special education feedback system
# This script carefully installs dependencies to avoid build errors

set -e  # Exit on error

# ANSI color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${BLUE}=== Installing core build tools ===${NC}"
pip install --upgrade pip setuptools wheel

echo "${BLUE}=== Installing NumPy with special handling ===${NC}"
# Use pre-built wheel for NumPy to avoid compilation issues
pip install numpy --no-build-isolation

echo "${BLUE}=== Installing core scientific packages ===${NC}"
# Install these one by one to avoid dependency conflicts
pip install pandas --no-build-isolation
pip install scipy --no-build-isolation
pip install scikit-learn --no-build-isolation

echo "${BLUE}=== Installing PyTorch (CPU version) ===${NC}"
# Use the official PyTorch index to get the right wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo "${BLUE}=== Installing NLP packages ===${NC}"
pip install transformers
pip install sentence-transformers

echo "${BLUE}=== Installing database drivers ===${NC}"
pip install PyMySQL cryptography

echo "${BLUE}=== Installing Flask and extensions (compatible version) ===${NC}"
# Install Flask 1.1.4 which is compatible with Airflow
pip install Flask==1.1.4
pip install flask-cors==3.0.10
pip install flask-sqlalchemy==2.5.1

echo "${BLUE}=== Installing remaining packages from requirements.txt ===${NC}"
# We'll use grep to exclude packages we've already installed
grep -v -E "numpy|pandas|scikit-learn|torch|sentence-transformers|flask|Flask" requirements.txt > temp_requirements.txt
pip install -r temp_requirements.txt

echo "${GREEN}=== Installation complete! ===${NC}"
echo "${YELLOW}If you encountered any errors, try installing the problematic package individually.${NC}"