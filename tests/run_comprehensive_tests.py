#!/usr/bin/env python3
"""
Comprehensive test runner for Contestlet API with coverage reporting
"""
import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


class TestRunner:
    """Comprehensive test runner with coverage and reporting"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"
        self.reports_dir = self.project_root / "test_reports"
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test categories and their directories
        self.test_categories = {
            "unit": self.tests_dir / "unit",
            "integration": self.tests_dir / "integration", 
            "api": self.tests_dir / "api",
            "e2e": self.tests_dir / "e2e",
            "security": self.tests_dir / "security",
            "performance": self.tests_dir / "performance",
            "multiple_winners": self.tests_dir / "api" / "test_multiple_winners_e2e.py",  # Specific test file
            "manual_entry": self.tests_dir / "e2e" / "test_manual_entry_e2e.py"  # Manual entry E2E tests
        }
        
        # Production readiness benchmarks
        self.benchmarks = {
            "coverage_threshold": 80,
            "security_tests_required": True,
            "performance_tests_required": True,
            "integration_tests_required": True,
            "max_test_duration": 300,  # 5 minutes
            "max_single_test_duration": 30  # 30 seconds
        }
    
    def install_dependencies(self) -> bool:
        """Install test dependencies"""
        print("📦 Installing test dependencies...")
        
        try:
            # Install test requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                str(self.tests_dir / "requirements.txt")
            ], check=True, capture_output=True)
            
            print("✅ Test dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install test dependencies: {e}")
            return False
    
    def run_linting(self) -> Dict[str, any]:
        """Run code linting and style checks"""
        print("🔍 Running linting and style checks...")
        
        results = {
            "passed": True,
            "issues": [],
            "tools": {}
        }
        
        # Run flake8 if available
        try:
            result = subprocess.run([
                "flake8", str(self.project_root / "app"), 
                "--max-line-length=120",
                "--ignore=E203,W503",
                "--format=json"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                results["tools"]["flake8"] = {"status": "passed", "issues": 0}
            else:
                issues = result.stdout.strip().split('\n') if result.stdout.strip() else []
                results["tools"]["flake8"] = {"status": "failed", "issues": len(issues)}
                results["issues"].extend(issues)
                results["passed"] = False
                
        except FileNotFoundError:
            results["tools"]["flake8"] = {"status": "not_available"}
        
        # Run black if available
        try:
            result = subprocess.run([
                "black", "--check", "--diff", str(self.project_root / "app")
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                results["tools"]["black"] = {"status": "passed"}
            else:
                results["tools"]["black"] = {"status": "failed", "diff": result.stdout}
                results["passed"] = False
                
        except FileNotFoundError:
            results["tools"]["black"] = {"status": "not_available"}
        
        return results
    
    def run_test_category(self, category: str, markers: List[str] = None, 
                         verbose: bool = False) -> Dict[str, any]:
        """Run tests for a specific category"""
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")
        
        test_dir = self.test_categories[category]
        if not test_dir.exists():
            return {
                "category": category,
                "status": "skipped",
                "reason": f"Test directory {test_dir} does not exist",
                "duration": 0,
                "tests_run": 0,
                "failures": 0,
                "errors": 0
            }
        
        print(f"🧪 Running {category} tests...")
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_dir),
            "-v" if verbose else "-q",
            "--tb=short",
            f"--junitxml={self.reports_dir}/{category}_results.xml",
            "--cov=app",
            f"--cov-report=html:{self.coverage_dir}_{category}",
            "--cov-report=xml",
            "--cov-report=term-missing"
        ]
        
        # Add markers if specified
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # Add timeout for performance tests
        if category == "performance":
            cmd.extend(["--timeout=60"])  # 60 second timeout per test
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            duration = time.time() - start_time
            
            # Parse results from XML if available
            xml_file = self.reports_dir / f"{category}_results.xml"
            test_stats = self._parse_junit_xml(xml_file) if xml_file.exists() else {}
            
            return {
                "category": category,
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                **test_stats
            }
            
        except Exception as e:
            return {
                "category": category,
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time,
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
    
    def _parse_junit_xml(self, xml_file: Path) -> Dict[str, any]:
        """Parse JUnit XML results"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            return {
                "tests_run": int(root.get("tests", 0)),
                "failures": int(root.get("failures", 0)),
                "errors": int(root.get("errors", 0)),
                "skipped": int(root.get("skipped", 0)),
                "time": float(root.get("time", 0))
            }
        except Exception:
            return {}
    
    def run_coverage_analysis(self) -> Dict[str, any]:
        """Run comprehensive coverage analysis"""
        print("📊 Running coverage analysis...")
        
        try:
            # Run pytest with coverage for all tests
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.tests_dir),
                "--cov=app",
                "--cov-report=html",
                "--cov-report=xml",
                "--cov-report=term-missing",
                "--cov-report=json",
                "-q"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            # Parse coverage results
            coverage_data = self._parse_coverage_results()
            
            return {
                "status": "completed",
                "overall_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                "lines_covered": coverage_data.get("totals", {}).get("covered_lines", 0),
                "lines_missing": coverage_data.get("totals", {}).get("missing_lines", 0),
                "files": coverage_data.get("files", {}),
                "meets_threshold": coverage_data.get("totals", {}).get("percent_covered", 0) >= self.benchmarks["coverage_threshold"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "overall_coverage": 0,
                "meets_threshold": False
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
    
    def run_security_audit(self) -> Dict[str, any]:
        """Run security audit checks"""
        print("🔒 Running security audit...")
        
        results = {
            "status": "completed",
            "tools": {},
            "vulnerabilities": [],
            "passed": True
        }
        
        # Run bandit security linter if available
        try:
            result = subprocess.run([
                "bandit", "-r", str(self.project_root / "app"),
                "-f", "json"
            ], capture_output=True, text=True)
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                results["tools"]["bandit"] = {
                    "status": "completed",
                    "issues": len(bandit_results.get("results", [])),
                    "high_severity": len([r for r in bandit_results.get("results", []) 
                                        if r.get("issue_severity") == "HIGH"]),
                    "medium_severity": len([r for r in bandit_results.get("results", []) 
                                          if r.get("issue_severity") == "MEDIUM"])
                }
                
                if bandit_results.get("results"):
                    results["vulnerabilities"].extend(bandit_results["results"])
                    results["passed"] = False
            
        except (FileNotFoundError, json.JSONDecodeError):
            results["tools"]["bandit"] = {"status": "not_available"}
        
        # Run safety check if available
        try:
            result = subprocess.run([
                "safety", "check", "--json"
            ], capture_output=True, text=True)
            
            if result.stdout:
                safety_results = json.loads(result.stdout)
                results["tools"]["safety"] = {
                    "status": "completed",
                    "vulnerabilities": len(safety_results)
                }
                
                if safety_results:
                    results["vulnerabilities"].extend(safety_results)
                    results["passed"] = False
            
        except (FileNotFoundError, json.JSONDecodeError):
            results["tools"]["safety"] = {"status": "not_available"}
        
        return results
    
    def generate_production_readiness_report(self, test_results: Dict[str, any]) -> Dict[str, any]:
        """Generate production readiness assessment"""
        print("📋 Generating production readiness report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "READY",
            "score": 0,
            "max_score": 100,
            "categories": {},
            "recommendations": [],
            "blockers": []
        }
        
        # Test Coverage (25 points)
        coverage = test_results.get("coverage", {})
        coverage_score = min(25, (coverage.get("overall_coverage", 0) / 100) * 25)
        report["categories"]["test_coverage"] = {
            "score": coverage_score,
            "max_score": 25,
            "status": "PASS" if coverage.get("meets_threshold", False) else "FAIL",
            "details": f"{coverage.get('overall_coverage', 0):.1f}% coverage"
        }
        
        if not coverage.get("meets_threshold", False):
            report["blockers"].append(f"Test coverage {coverage.get('overall_coverage', 0):.1f}% below threshold {self.benchmarks['coverage_threshold']}%")
        
        # Test Categories (40 points total)
        category_scores = {
            "unit": 10,
            "integration": 10,
            "api": 10,
            "security": 5,
            "performance": 5
        }
        
        total_category_score = 0
        for category, max_score in category_scores.items():
            category_result = test_results.get("categories", {}).get(category, {})
            
            if category_result.get("status") == "passed":
                score = max_score
                status = "PASS"
            elif category_result.get("status") == "skipped":
                score = 0
                status = "SKIP"
            else:
                score = 0
                status = "FAIL"
                report["blockers"].append(f"{category.title()} tests failed")
            
            total_category_score += score
            report["categories"][f"{category}_tests"] = {
                "score": score,
                "max_score": max_score,
                "status": status,
                "details": f"{category_result.get('tests_run', 0)} tests run, {category_result.get('failures', 0)} failures"
            }
        
        # Security Audit (20 points)
        security = test_results.get("security_audit", {})
        security_score = 20 if security.get("passed", False) else 0
        report["categories"]["security_audit"] = {
            "score": security_score,
            "max_score": 20,
            "status": "PASS" if security.get("passed", False) else "FAIL",
            "details": f"{len(security.get('vulnerabilities', []))} vulnerabilities found"
        }
        
        if not security.get("passed", False):
            report["blockers"].append(f"Security vulnerabilities found: {len(security.get('vulnerabilities', []))}")
        
        # Code Quality (15 points)
        linting = test_results.get("linting", {})
        quality_score = 15 if linting.get("passed", False) else 10
        report["categories"]["code_quality"] = {
            "score": quality_score,
            "max_score": 15,
            "status": "PASS" if linting.get("passed", False) else "WARN",
            "details": f"{len(linting.get('issues', []))} linting issues"
        }
        
        if not linting.get("passed", False):
            report["recommendations"].append("Fix code linting issues for better maintainability")
        
        # Calculate total score
        report["score"] = coverage_score + total_category_score + security_score + quality_score
        
        # Determine overall status
        if report["blockers"]:
            report["overall_status"] = "NOT_READY"
        elif report["score"] < 80:
            report["overall_status"] = "NEEDS_IMPROVEMENT"
        else:
            report["overall_status"] = "READY"
        
        return report
    
    def save_reports(self, test_results: Dict[str, any], production_report: Dict[str, any]):
        """Save test reports to files"""
        print("💾 Saving test reports...")
        
        # Save detailed test results
        with open(self.reports_dir / "test_results.json", 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Save production readiness report
        with open(self.reports_dir / "production_readiness.json", 'w') as f:
            json.dump(production_report, f, indent=2, default=str)
        
        # Generate HTML report
        self._generate_html_report(test_results, production_report)
        
        print(f"📊 Reports saved to {self.reports_dir}")
    
    def _generate_html_report(self, test_results: Dict[str, any], production_report: Dict[str, any]):
        """Generate HTML report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Contestlet API - Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .status-ready {{ color: #28a745; }}
        .status-not-ready {{ color: #dc3545; }}
        .status-needs-improvement {{ color: #ffc107; }}
        .category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ background: #d4edda; }}
        .fail {{ background: #f8d7da; }}
        .warn {{ background: #fff3cd; }}
        .skip {{ background: #e2e3e5; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .details {{ margin-top: 10px; font-size: 14px; }}
        .blockers {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Contestlet API - Test Results</h1>
        <p><strong>Generated:</strong> {production_report['timestamp']}</p>
        <p class="status-{production_report['overall_status'].lower().replace('_', '-')}">
            <strong>Status:</strong> {production_report['overall_status'].replace('_', ' ')}
        </p>
        <p class="score">Score: {production_report['score']}/{production_report['max_score']}</p>
    </div>
    
    {self._generate_blockers_html(production_report)}
    {self._generate_recommendations_html(production_report)}
    {self._generate_categories_html(production_report)}
    {self._generate_detailed_results_html(test_results)}
</body>
</html>
        """
        
        with open(self.reports_dir / "test_report.html", 'w') as f:
            f.write(html_content)
    
    def _generate_blockers_html(self, report: Dict[str, any]) -> str:
        """Generate HTML for blockers section"""
        if not report.get("blockers"):
            return ""
        
        blockers_html = '<div class="blockers"><h2>🚫 Production Blockers</h2><ul>'
        for blocker in report["blockers"]:
            blockers_html += f"<li>{blocker}</li>"
        blockers_html += "</ul></div>"
        return blockers_html
    
    def _generate_recommendations_html(self, report: Dict[str, any]) -> str:
        """Generate HTML for recommendations section"""
        if not report.get("recommendations"):
            return ""
        
        rec_html = '<div class="recommendations"><h2>💡 Recommendations</h2><ul>'
        for rec in report["recommendations"]:
            rec_html += f"<li>{rec}</li>"
        rec_html += "</ul></div>"
        return rec_html
    
    def _generate_categories_html(self, report: Dict[str, any]) -> str:
        """Generate HTML for categories section"""
        categories_html = "<h2>📊 Test Categories</h2>"
        
        for category, details in report["categories"].items():
            status_class = details["status"].lower()
            categories_html += f"""
            <div class="category {status_class}">
                <h3>{category.replace('_', ' ').title()}</h3>
                <p><strong>Score:</strong> {details['score']}/{details['max_score']}</p>
                <p><strong>Status:</strong> {details['status']}</p>
                <div class="details">{details['details']}</div>
            </div>
            """
        
        return categories_html
    
    def _generate_detailed_results_html(self, test_results: Dict[str, any]) -> str:
        """Generate HTML for detailed test results"""
        return """
        <h2>📋 Detailed Results</h2>
        <p>See <code>test_results.json</code> for complete test output and logs.</p>
        """
    
    def run_all_tests(self, categories: List[str] = None, verbose: bool = False, 
                     skip_deps: bool = False) -> Dict[str, any]:
        """Run comprehensive test suite"""
        print("🚀 Starting comprehensive test suite...")
        start_time = time.time()
        
        # Install dependencies
        if not skip_deps and not self.install_dependencies():
            return {"status": "error", "error": "Failed to install dependencies"}
        
        results = {
            "start_time": start_time,
            "categories": {},
            "linting": {},
            "coverage": {},
            "security_audit": {},
            "total_duration": 0
        }
        
        # Run linting
        results["linting"] = self.run_linting()
        
        # Run test categories
        categories_to_run = categories or list(self.test_categories.keys())
        
        for category in categories_to_run:
            results["categories"][category] = self.run_test_category(category, verbose=verbose)
        
        # Run coverage analysis
        results["coverage"] = self.run_coverage_analysis()
        
        # Run security audit
        results["security_audit"] = self.run_security_audit()
        
        # Calculate total duration
        results["total_duration"] = time.time() - start_time
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for Contestlet API")
    
    parser.add_argument("--categories", nargs="+", 
                       choices=["unit", "integration", "api", "security", "performance"],
                       help="Test categories to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    parser.add_argument("--coverage-only", action="store_true",
                       help="Run only coverage analysis")
    parser.add_argument("--lint-only", action="store_true",
                       help="Run only linting")
    parser.add_argument("--security-only", action="store_true",
                       help="Run only security audit")
    parser.add_argument("--production-check", action="store_true",
                       help="Full production readiness check")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.coverage_only:
        results = {"coverage": runner.run_coverage_analysis()}
    elif args.lint_only:
        results = {"linting": runner.run_linting()}
    elif args.security_only:
        results = {"security_audit": runner.run_security_audit()}
    else:
        results = runner.run_all_tests(
            categories=args.categories,
            verbose=args.verbose,
            skip_deps=args.skip_deps
        )
    
    # Generate production readiness report
    if args.production_check or not any([args.coverage_only, args.lint_only, args.security_only]):
        production_report = runner.generate_production_readiness_report(results)
        runner.save_reports(results, production_report)
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 PRODUCTION READINESS SUMMARY")
        print("="*60)
        print(f"Overall Status: {production_report['overall_status']}")
        print(f"Score: {production_report['score']}/{production_report['max_score']}")
        
        if production_report["blockers"]:
            print("\n🚫 BLOCKERS:")
            for blocker in production_report["blockers"]:
                print(f"  - {blocker}")
        
        if production_report["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in production_report["recommendations"]:
                print(f"  - {rec}")
        
        print(f"\n📊 Full report: {runner.reports_dir}/test_report.html")
        
        # Exit with appropriate code
        if production_report["overall_status"] == "NOT_READY":
            sys.exit(1)
        elif production_report["overall_status"] == "NEEDS_IMPROVEMENT":
            sys.exit(2)
        else:
            sys.exit(0)
    
    else:
        # Print simple results for single-category runs
        for category, result in results.items():
            if isinstance(result, dict) and "status" in result:
                print(f"{category}: {result['status']}")


if __name__ == "__main__":
    main()
