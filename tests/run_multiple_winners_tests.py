#!/usr/bin/env python3
"""
Multiple Winners Feature Test Runner

Comprehensive test runner specifically for the multiple winners feature.
Runs all related tests including unit, integration, and E2E tests.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


class MultipleWinnersTestRunner:
    """Test runner for multiple winners feature"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = Path(__file__).parent
        
        # Multiple winners test files
        self.test_files = {
            "unit": self.tests_dir / "unit" / "test_winner_service.py",
            "integration": self.tests_dir / "integration" / "test_multiple_winners_integration.py",
            "e2e": self.tests_dir / "api" / "test_multiple_winners_e2e.py",
            "original": self.tests_dir / "test_multiple_winners.py"
        }
    
    def run_test_file(self, test_type: str, verbose: bool = True) -> dict:
        """Run a specific test file"""
        if test_type not in self.test_files:
            raise ValueError(f"Unknown test type: {test_type}")
        
        test_file = self.test_files[test_type]
        if not test_file.exists():
            return {
                "status": "skipped",
                "reason": f"Test file {test_file} does not exist",
                "duration": 0
            }
        
        print(f"🧪 Running {test_type} tests: {test_file.name}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v" if verbose else "-q",
            "--tb=short",
            "--cov=app.core.services.winner_service",
            "--cov=app.models.contest_winner", 
            "--cov=app.routers.contest_winners",
            "--cov=app.schemas.contest_winner",
            "--cov-report=term-missing"
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            duration = time.time() - start_time
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": duration,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def run_all_multiple_winner_tests(self, verbose: bool = True) -> dict:
        """Run all multiple winner tests"""
        print("🏆 Running Multiple Winners Feature Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        # Run each test category
        for test_type in self.test_files.keys():
            results[test_type] = self.run_test_file(test_type, verbose)
        
        total_duration = time.time() - start_time
        
        # Calculate summary
        passed = sum(1 for r in results.values() if r["status"] == "passed")
        failed = sum(1 for r in results.values() if r["status"] == "failed")
        skipped = sum(1 for r in results.values() if r["status"] == "skipped")
        errors = sum(1 for r in results.values() if r["status"] == "error")
        
        summary = {
            "total_duration": total_duration,
            "test_categories": len(self.test_files),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "overall_status": "PASSED" if failed == 0 and errors == 0 else "FAILED"
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 MULTIPLE WINNERS TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Test Categories: {summary['test_categories']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Errors: {summary['errors']}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        print("\n📋 Category Details:")
        for test_type, result in results.items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌", 
                "skipped": "⏭️",
                "error": "💥"
            }.get(result["status"], "❓")
            
            print(f"  {status_emoji} {test_type.ljust(12)}: {result['status'].upper()}")
            if result["status"] in ["failed", "error"]:
                print(f"     Duration: {result['duration']:.2f}s")
        
        return {
            "summary": summary,
            "results": results
        }
    
    def run_specific_test_patterns(self, patterns: list, verbose: bool = True) -> dict:
        """Run tests matching specific patterns"""
        print(f"🎯 Running Multiple Winners tests matching patterns: {patterns}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--cov=app.core.services.winner_service",
            "--cov=app.models.contest_winner",
            "--cov=app.routers.contest_winners", 
            "--cov=app.schemas.contest_winner",
            "--cov-report=term-missing"
        ]
        
        # Add pattern matching
        for pattern in patterns:
            cmd.extend(["-k", pattern])
        
        # Add all test files
        for test_file in self.test_files.values():
            if test_file.exists():
                cmd.append(str(test_file))
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            duration = time.time() - start_time
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": duration,
                "return_code": result.returncode,
                "patterns": patterns
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time,
                "patterns": patterns
            }
    
    def run_performance_tests(self) -> dict:
        """Run performance-focused tests for multiple winners"""
        print("⚡ Running Multiple Winners Performance Tests")
        
        patterns = [
            "test_large_contest_performance",
            "test_performance",
            "performance"
        ]
        
        return self.run_specific_test_patterns(patterns, verbose=True)
    
    def run_edge_case_tests(self) -> dict:
        """Run edge case and error handling tests"""
        print("🔍 Running Multiple Winners Edge Case Tests")
        
        patterns = [
            "test_error",
            "test_insufficient",
            "test_duplicate", 
            "test_not_found",
            "edge_case"
        ]
        
        return self.run_specific_test_patterns(patterns, verbose=True)
    
    def validate_feature_completeness(self) -> dict:
        """Validate that all required multiple winner functionality is tested"""
        print("📋 Validating Multiple Winners Feature Test Completeness")
        
        required_test_patterns = [
            "test_single_winner",
            "test_multiple_winner", 
            "test_prize_tiers",
            "test_winner_reselection",
            "test_winner_management",
            "test_winner_notification",
            "test_backward_compatibility",
            "test_database_schema",
            "test_api_integration"
        ]
        
        results = {}
        
        for pattern in required_test_patterns:
            print(f"  Checking: {pattern}")
            result = self.run_specific_test_patterns([pattern], verbose=False)
            results[pattern] = result["status"] == "passed"
        
        completeness_score = sum(results.values()) / len(results) * 100
        
        print(f"\n📊 Feature Completeness: {completeness_score:.1f}%")
        
        missing_tests = [pattern for pattern, passed in results.items() if not passed]
        if missing_tests:
            print("❌ Missing or failing test patterns:")
            for pattern in missing_tests:
                print(f"  - {pattern}")
        else:
            print("✅ All required test patterns are present and passing")
        
        return {
            "completeness_score": completeness_score,
            "required_patterns": len(required_test_patterns),
            "passing_patterns": sum(results.values()),
            "missing_patterns": missing_tests,
            "is_complete": completeness_score >= 90
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multiple Winners Feature Test Runner")
    
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "original", "all"],
                       default="all", help="Test type to run")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--edge-cases", action="store_true", 
                       help="Run edge case tests only")
    parser.add_argument("--validate", action="store_true",
                       help="Validate feature test completeness")
    parser.add_argument("--patterns", nargs="+",
                       help="Run tests matching specific patterns")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Quiet output")
    
    args = parser.parse_args()
    
    runner = MultipleWinnersTestRunner()
    
    try:
        if args.validate:
            result = runner.validate_feature_completeness()
            exit_code = 0 if result["is_complete"] else 1
            
        elif args.performance:
            result = runner.run_performance_tests()
            exit_code = 0 if result["status"] == "passed" else 1
            
        elif args.edge_cases:
            result = runner.run_edge_case_tests()
            exit_code = 0 if result["status"] == "passed" else 1
            
        elif args.patterns:
            result = runner.run_specific_test_patterns(args.patterns, verbose=not args.quiet)
            exit_code = 0 if result["status"] == "passed" else 1
            
        elif args.type == "all":
            result = runner.run_all_multiple_winner_tests(verbose=not args.quiet)
            exit_code = 0 if result["summary"]["overall_status"] == "PASSED" else 1
            
        else:
            result = runner.run_test_file(args.type, verbose=not args.quiet)
            exit_code = 0 if result["status"] == "passed" else 1
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
