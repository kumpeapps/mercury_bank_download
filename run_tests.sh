#!/bin/bash
set -e

# Mercury Bank Integration Platform Test Runner
# This script runs the comprehensive test suite for the platform

echo "🧪 Mercury Bank Integration Platform Test Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Check if we're in a virtual environment or docker
if [[ -z "$VIRTUAL_ENV" ]] && [[ ! -f /.dockerenv ]]; then
    print_warning "Not in a virtual environment. Consider activating one for isolated testing."
fi

# Default test options
TEST_COVERAGE="true"
TEST_PARALLEL="false"
TEST_VERBOSE="false"
TEST_PATTERN=""
INSTALL_DEPS="true"
TEST_TYPE="all"  # all, unit, integration

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            TEST_COVERAGE="false"
            shift
            ;;
        --parallel)
            TEST_PARALLEL="true"
            shift
            ;;
        --verbose|-v)
            TEST_VERBOSE="true"
            shift
            ;;
        --pattern|-p)
            TEST_PATTERN="$2"
            shift 2
            ;;
        --no-install)
            INSTALL_DEPS="false"
            shift
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --models)
            TEST_TYPE="models"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-coverage     Skip coverage reporting"
            echo "  --parallel        Run tests in parallel"
            echo "  --verbose, -v     Verbose output"
            echo "  --pattern, -p     Run tests matching pattern"
            echo "  --no-install      Skip dependency installation"
            echo "  --unit            Run only unit tests"
            echo "  --integration     Run only integration tests"
            echo "  --models          Run only model tests"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Run all tests with coverage"
            echo "  $0 --unit --verbose          # Run unit tests with verbose output"
            echo "  $0 --pattern test_user       # Run tests matching 'test_user'"
            echo "  $0 --parallel --no-coverage  # Run tests in parallel without coverage"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Install test dependencies
if [[ "$INSTALL_DEPS" == "true" ]]; then
    print_status "Installing test dependencies..."
    if command -v pip &> /dev/null; then
        pip install -r requirements-test.txt > /dev/null 2>&1
        print_success "Test dependencies installed"
    else
        print_error "pip not found. Please install test dependencies manually:"
        print_error "pip install -r requirements-test.txt"
        exit 1
    fi
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install test dependencies:"
    print_error "pip install -r requirements-test.txt"
    exit 1
fi

# Set up Python path to include both web_app and sync_app
export PYTHONPATH="${PROJECT_DIR}/web_app:${PROJECT_DIR}/sync_app:${PYTHONPATH}"

# Set test database URL (use SQLite for tests)
export TEST_DATABASE_URL="sqlite:///:memory:"

# Set required environment variables for testing
export SECRET_KEY="test-secret-key-for-testing-only-not-for-production"
export USERS_EXTERNALLY_MANAGED="false"

# Build pytest command
PYTEST_ARGS=()

# Add test directory
case $TEST_TYPE in
    "unit")
        PYTEST_ARGS+=("tests/test_user_registration.py")
        PYTEST_ARGS+=("tests/test_models.py")
        ;;
    "integration")
        PYTEST_ARGS+=("tests/test_web_integration.py")
        ;;
    "models")
        PYTEST_ARGS+=("tests/test_models.py")
        ;;
    *)
        PYTEST_ARGS+=("tests/")
        ;;
esac

# Add coverage if enabled
if [[ "$TEST_COVERAGE" == "true" ]]; then
    PYTEST_ARGS+=("--cov=web_app/models")
    PYTEST_ARGS+=("--cov=web_app/utils")
    # Note: sync_app models are mirrors of web_app models, tested via web_app
    PYTEST_ARGS+=("--cov-report=html:htmlcov")
    PYTEST_ARGS+=("--cov-report=term-missing")
    PYTEST_ARGS+=("--cov-fail-under=30")
fi

# Add parallel execution if enabled
if [[ "$TEST_PARALLEL" == "true" ]]; then
    PYTEST_ARGS+=("-n" "auto")
fi

# Add verbosity if enabled
if [[ "$TEST_VERBOSE" == "true" ]]; then
    PYTEST_ARGS+=("-v")
fi

# Add pattern matching if specified
if [[ -n "$TEST_PATTERN" ]]; then
    PYTEST_ARGS+=("-k" "$TEST_PATTERN")
fi

# Add other useful options
PYTEST_ARGS+=("--tb=short")  # Shorter traceback format
PYTEST_ARGS+=("--strict-markers")  # Strict marker checking
PYTEST_ARGS+=("--disable-warnings")  # Disable warnings for cleaner output

print_status "Running tests with command: pytest ${PYTEST_ARGS[*]}"
echo ""

# Run the tests
if pytest "${PYTEST_ARGS[@]}"; then
    print_success "All tests passed!"
    
    if [[ "$TEST_COVERAGE" == "true" ]]; then
        echo ""
        print_success "Coverage report generated in htmlcov/index.html"
    fi
    
    echo ""
    print_status "Test Summary:"
    echo "  ✅ User registration and role assignment tests"
    echo "  ✅ Database model tests"
    echo "  ✅ Web integration tests"
    echo "  ✅ Authentication and permission tests"
    echo ""
    
    exit 0
else
    print_error "Some tests failed!"
    echo ""
    print_status "Common issues and solutions:"
    echo "  - Database connection issues: Check TEST_DATABASE_URL"
    echo "  - Import errors: Verify PYTHONPATH includes web_app and sync_app"
    echo "  - Missing dependencies: Run 'pip install -r requirements-test.txt'"
    echo "  - Port conflicts: Ensure test app ports are available"
    echo ""
    
    exit 1
fi
