#!/usr/bin/env python3
"""
Comprehensive test runner for Contestlet API
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(command)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    
    # Install test requirements
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "tests/requirements.txt"], 
                      "Installing test dependencies"):
        return False
    
    return True


def run_unit_tests():
    """Run unit tests"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--tb=short",
        "--cov=app.core",
        "--cov-report=term-missing"
    ], "Running unit tests")


def run_api_tests():
    """Run API tests"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/api/", 
        "-v", 
        "--tb=short",
        "--cov=app.routers",
        "--cov-report=term-missing"
    ], "Running API tests")


def run_security_tests():
    """Run security tests"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/security/", 
        "-v", 
        "--tb=short",
        "--cov=app.core.auth",
        "--cov-report=term-missing"
    ], "Running security tests")


def run_performance_tests():
    """Run performance tests"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/performance/", 
        "-v", 
        "--tb=short",
        "-m", "performance"
    ], "Running performance tests")


def run_integration_tests():
    """Run integration tests"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/integration/", 
        "-v", 
        "--tb=short",
        "--cov=app.services",
        "--cov-report=term-missing"
    ], "Running integration tests")


def run_all_tests():
    """Run all tests with coverage"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=80"
    ], "Running all tests with coverage")


def run_smoke_tests():
    """Run smoke tests (quick validation)"""
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short",
        "-m", "smoke",
        "--maxfail=5"
    ], "Running smoke tests")


def generate_coverage_report():
    """Generate detailed coverage report"""
    return run_command([
        sys.executable, "-m", "coverage", "report", "--show-missing"
    ], "Generating coverage report")


def run_linting():
    """Run code linting"""
    # Check if flake8 is available
    try:
        return run_command([
            sys.executable, "-m", "flake8", "app/", "--max-line-length=100", "--ignore=E203,W503"
        ], "Running code linting")
    except FileNotFoundError:
        print("⚠️  flake8 not available, skipping linting")
        return True


def run_type_checking():
    """Run type checking"""
    # Check if mypy is available
    try:
        return run_command([
            sys.executable, "-m", "mypy", "app/", "--ignore-missing-imports"
        ], "Running type checking")
    except FileNotFoundError:
        print("⚠️  mypy not available, skipping type checking")
        return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Contestlet API Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--types", action="store_true", help="Run type checking")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    
    args = parser.parse_args()
    
    print("🧪 CONTESTLET API - COMPREHENSIVE TEST RUNNER")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)
    
    success = True
    
    # Run specific test categories
    if args.unit:
        success &= run_unit_tests()
    elif args.api:
        success &= run_api_tests()
    elif args.security:
        success &= run_security_tests()
    elif args.performance:
        success &= run_performance_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.smoke:
        success &= run_smoke_tests()
    else:
        # Default: run all tests
        success &= run_all_tests()
    
    # Additional checks
    if args.coverage:
        success &= generate_coverage_report()
    
    if args.lint:
        success &= run_linting()
    
    if args.types:
        success &= run_type_checking()
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Contestlet API is production ready!")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please fix the failing tests before deployment")
        sys.exit(1)


if __name__ == "__main__":
    main()
