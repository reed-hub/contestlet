#!/usr/bin/env python3
"""
Production-ready test runner for Contestlet API
Ensures 100% pass rate for production deployment
"""
import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional


class ProductionTestRunner:
    """Production test runner with comprehensive validation"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
        
        # Production test categories
        self.test_categories = {
            "smoke": "Quick validation tests",
            "e2e": "End-to-end production tests", 
            "security": "Security validation tests",
            "performance": "Performance benchmark tests"
        }
        
        # Production requirements
        self.requirements = {
            "min_coverage": 80,
            "max_test_duration": 300,  # 5 minutes
            "max_single_test_duration": 30,  # 30 seconds
            "required_endpoints": [
                "/health",
                "/",
                "/contests/active",
                "/auth/request-otp"
            ]
        }
    
    def check_server_running(self) -> bool:
        """Check if the API server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_server_if_needed(self) -> bool:
        """Start the API server if not running"""
        if self.check_server_running():
            print("✅ API server is already running")
            return True
        
        print("🚀 Starting API server...")
        try:
            # Start server in background
            subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", "0.0.0.0", "--port", "8000"
            ], cwd=self.project_root)
            
            # Wait for server to start
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.check_server_running():
                    print("✅ API server started successfully")
                    return True
            
            print("❌ Failed to start API server")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def run_smoke_tests(self) -> Dict[str, any]:
        """Run smoke tests for quick validation"""
        print("🔥 Running smoke tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "api" / "test_production_e2e.py::TestProductionSmoke"),
            "-v", "-m", "smoke",
            "--tb=short",
            f"--junitxml={self.reports_dir}/smoke_results.xml"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "category": "smoke",
            "status": "passed" if result.returncode == 0 else "failed",
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def run_e2e_tests(self) -> Dict[str, any]:
        """Run end-to-end tests"""
        print("🔄 Running E2E tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "api" / "test_production_e2e.py::TestProductionE2EEndpoints"),
            "-v", "-m", "e2e",
            "--tb=short",
            f"--junitxml={self.reports_dir}/e2e_results.xml"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "category": "e2e",
            "status": "passed" if result.returncode == 0 else "failed",
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def run_security_tests(self) -> Dict[str, any]:
        """Run security tests"""
        print("🔒 Running security tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "api" / "test_production_e2e.py::TestProductionSecurity"),
            "-v", "-m", "security",
            "--tb=short",
            f"--junitxml={self.reports_dir}/security_results.xml"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "category": "security",
            "status": "passed" if result.returncode == 0 else "failed",
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def run_performance_tests(self) -> Dict[str, any]:
        """Run performance tests"""
        print("⚡ Running performance tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "api" / "test_production_e2e.py::TestProductionPerformance"),
            "-v", "-m", "performance",
            "--tb=short",
            f"--junitxml={self.reports_dir}/performance_results.xml"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "category": "performance",
            "status": "passed" if result.returncode == 0 else "failed",
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def run_coverage_analysis(self) -> Dict[str, any]:
        """Run coverage analysis"""
        print("📊 Running coverage analysis...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "api" / "test_production_e2e.py"),
            "--cov=app",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=json",
            "--cov-report=term-missing",
            "-q"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        
        # Parse coverage results
        coverage_data = self._parse_coverage_results()
        
        return {
            "status": "completed",
            "overall_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
            "meets_threshold": coverage_data.get("totals", {}).get("percent_covered", 0) >= self.requirements["min_coverage"]
        }
    
    def _parse_coverage_results(self) -> Dict[str, any]:
        """Parse coverage.json results"""
        coverage_file = self.project_root / "coverage.json"
        
        if not coverage_file.exists():
            return {}
        
        try:
            with open(coverage_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def validate_critical_endpoints(self) -> Dict[str, any]:
        """Validate critical endpoints are working"""
        print("🔍 Validating critical endpoints...")
        
        try:
            import requests
            results = {}
            
            for endpoint in self.requirements["required_endpoints"]:
                try:
                    response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                    results[endpoint] = {
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                        "working": response.status_code == 200
                    }
                except Exception as e:
                    results[endpoint] = {
                        "status_code": None,
                        "response_time": None,
                        "working": False,
                        "error": str(e)
                    }
            
            all_working = all(result["working"] for result in results.values())
            
            return {
                "status": "passed" if all_working else "failed",
                "endpoints": results,
                "all_working": all_working
            }
            
        except ImportError:
            return {
                "status": "skipped",
                "reason": "requests library not available"
            }
    
    def generate_production_report(self, test_results: Dict[str, any]) -> Dict[str, any]:
        """Generate production readiness report"""
        print("📋 Generating production readiness report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "READY",
            "score": 0,
            "max_score": 100,
            "categories": {},
            "blockers": [],
            "warnings": []
        }
        
        # Test Results (60 points)
        test_score = 0
        category_scores = {"smoke": 15, "e2e": 20, "security": 15, "performance": 10}
        
        for category, max_score in category_scores.items():
            result = test_results.get(category, {})
            if result.get("status") == "passed":
                score = max_score
                status = "PASS"
            else:
                score = 0
                status = "FAIL"
                report["blockers"].append(f"{category.title()} tests failed")
            
            test_score += score
            report["categories"][f"{category}_tests"] = {
                "score": score,
                "max_score": max_score,
                "status": status
            }
        
        # Coverage (20 points)
        coverage = test_results.get("coverage", {})
        coverage_score = 20 if coverage.get("meets_threshold", False) else 0
        report["categories"]["coverage"] = {
            "score": coverage_score,
            "max_score": 20,
            "status": "PASS" if coverage.get("meets_threshold", False) else "FAIL",
            "details": f"{coverage.get('overall_coverage', 0):.1f}% coverage"
        }
        
        if not coverage.get("meets_threshold", False):
            report["blockers"].append(f"Coverage {coverage.get('overall_coverage', 0):.1f}% below {self.requirements['min_coverage']}%")
        
        # Endpoint Validation (20 points)
        endpoints = test_results.get("endpoints", {})
        endpoint_score = 20 if endpoints.get("all_working", False) else 0
        report["categories"]["endpoints"] = {
            "score": endpoint_score,
            "max_score": 20,
            "status": "PASS" if endpoints.get("all_working", False) else "FAIL"
        }
        
        if not endpoints.get("all_working", False):
            report["blockers"].append("Critical endpoints not responding")
        
        # Calculate total score
        report["score"] = test_score + coverage_score + endpoint_score
        
        # Determine overall status
        if report["blockers"]:
            report["overall_status"] = "NOT_READY"
        elif report["score"] < 90:
            report["overall_status"] = "NEEDS_IMPROVEMENT"
        else:
            report["overall_status"] = "READY"
        
        return report
    
    def save_report(self, report: Dict[str, any]):
        """Save production readiness report"""
        # Save JSON report
        with open(self.reports_dir / "production_readiness.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save HTML report
        html_content = self._generate_html_report(report)
        with open(self.reports_dir / "production_report.html", 'w') as f:
            f.write(html_content)
        
        print(f"📊 Reports saved to {self.reports_dir}")
    
    def _generate_html_report(self, report: Dict[str, any]) -> str:
        """Generate HTML report"""
        status_class = report["overall_status"].lower().replace("_", "-")
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Contestlet API - Production Readiness Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .status-ready {{ color: #28a745; }}
        .status-not-ready {{ color: #dc3545; }}
        .status-needs-improvement {{ color: #ffc107; }}
        .category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ background: #d4edda; }}
        .fail {{ background: #f8d7da; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .blockers {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Contestlet API - Production Readiness Report</h1>
        <p><strong>Generated:</strong> {report['timestamp']}</p>
        <p class="status-{status_class}">
            <strong>Status:</strong> {report['overall_status'].replace('_', ' ')}
        </p>
        <p class="score">Score: {report['score']}/{report['max_score']}</p>
    </div>
    
    {"".join([f'<div class="blockers"><h2>🚫 Production Blockers</h2><ul>{"".join([f"<li>{blocker}</li>" for blocker in report["blockers"]])}</ul></div>' if report.get("blockers") else ""])}
    
    <h2>📊 Test Categories</h2>
    {"".join([f'''
    <div class="category {details["status"].lower()}">
        <h3>{category.replace('_', ' ').title()}</h3>
        <p><strong>Score:</strong> {details["score"]}/{details["max_score"]}</p>
        <p><strong>Status:</strong> {details["status"]}</p>
    </div>
    ''' for category, details in report["categories"].items()])}
</body>
</html>
        """
    
    def run_production_tests(self) -> bool:
        """Run complete production test suite"""
        print("🚀 Starting production test suite...")
        start_time = time.time()
        
        # Check if server is running
        if not self.start_server_if_needed():
            print("❌ Cannot run tests without API server")
            return False
        
        # Wait a moment for server to be fully ready
        time.sleep(2)
        
        results = {}
        
        # Run test categories
        results["smoke"] = self.run_smoke_tests()
        results["e2e"] = self.run_e2e_tests()
        results["security"] = self.run_security_tests()
        results["performance"] = self.run_performance_tests()
        
        # Run coverage analysis
        results["coverage"] = self.run_coverage_analysis()
        
        # Validate endpoints
        results["endpoints"] = self.validate_critical_endpoints()
        
        # Generate report
        report = self.generate_production_report(results)
        self.save_report(report)
        
        # Print summary
        total_duration = time.time() - start_time
        print("\n" + "="*60)
        print("🎯 PRODUCTION READINESS SUMMARY")
        print("="*60)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Score: {report['score']}/{report['max_score']}")
        print(f"Duration: {total_duration:.1f} seconds")
        
        if report["blockers"]:
            print("\n🚫 BLOCKERS:")
            for blocker in report["blockers"]:
                print(f"  - {blocker}")
        
        print(f"\n📊 Full report: {self.reports_dir}/production_report.html")
        
        # Return success status
        return report["overall_status"] == "READY"


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production test runner for Contestlet API")
    parser.add_argument("--smoke-only", action="store_true", help="Run only smoke tests")
    parser.add_argument("--no-server-start", action="store_true", help="Don't start server automatically")
    
    args = parser.parse_args()
    
    runner = ProductionTestRunner()
    
    if args.smoke_only:
        # Run only smoke tests
        if not args.no_server_start:
            if not runner.start_server_if_needed():
                sys.exit(1)
        
        result = runner.run_smoke_tests()
        if result["status"] == "passed":
            print("✅ Smoke tests passed")
            sys.exit(0)
        else:
            print("❌ Smoke tests failed")
            sys.exit(1)
    else:
        # Run full production test suite
        success = runner.run_production_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
