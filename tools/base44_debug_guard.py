#!/usr/bin/env python3
"""
Base44 Debug Guard - Live-Only Master Prompt Implementation
Comprehensive Cannot-Fail Debug System

Mission: Ensure 100% production readiness with zero tolerance for failures
Two-Pass Audit System with verification loops
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_guard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Base44DebugGuard:
    """Comprehensive debug guard with two-pass audit system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        self.verification_results = {}
        
    def log_error(self, message: str, details: str = None):
        """Log error with details"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'details': details or ''
        }
        self.errors.append(error_entry)
        logger.error(f"{message} - {details}")
        
    def log_warning(self, message: str, details: str = None):
        """Log warning with details"""
        warning_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'details': details or ''
        }
        self.warnings.append(warning_entry)
        logger.warning(f"{message} - {details}")
        
    def log_fix(self, message: str, action: str = None):
        """Log applied fix"""
        fix_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'action': action or ''
        }
        self.fixes_applied.append(fix_entry)
        logger.info(f"FIX APPLIED: {message} - {action}")
        
    def check_python_dependencies(self) -> bool:
        """Check and install missing Python dependencies"""
        logger.info("=== CHECKING PYTHON DEPENDENCIES ===")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'python-dotenv',
            'loguru',
            'opencv-python',
            'passlib',
            'python-multipart',
            'jinja2',
            'aiofiles'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✓ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                self.log_warning(f"Missing package: {package}")
                
        if missing_packages:
            logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install'
                ] + missing_packages, check=True, capture_output=True, text=True)
                self.log_fix(f"Installed packages: {', '.join(missing_packages)}")
                return True
            except subprocess.CalledProcessError as e:
                self.log_error(f"Failed to install packages: {e.stderr}")
                return False
        
        return True
        
    def check_environment_files(self) -> bool:
        """Check and validate environment files"""
        logger.info("=== CHECKING ENVIRONMENT FILES ===")
        
        env_files = ['.env.production', '.env.runtime']
        all_valid = True
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if not env_path.exists():
                self.log_error(f"Missing environment file: {env_file}")
                all_valid = False
            else:
                logger.info(f"✓ {env_file} exists")
                
        return all_valid
        
    def check_syntax_errors(self) -> bool:
        """Check for Python syntax errors"""
        logger.info("=== CHECKING SYNTAX ERRORS ===")
        
        python_files = list(self.project_root.rglob('*.py'))
        syntax_errors = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
                logger.info(f"✓ {py_file.relative_to(self.project_root)} - syntax OK")
            except SyntaxError as e:
                error_msg = f"Syntax error in {py_file}: {e}"
                self.log_error(error_msg)
                syntax_errors.append((py_file, e))
            except Exception as e:
                self.log_warning(f"Could not check {py_file}: {e}")
                
        return len(syntax_errors) == 0
        
    def check_event_loop_issues(self) -> bool:
        """Check for event loop configuration issues"""
        logger.info("=== CHECKING EVENT LOOP ISSUES ===")
        
        main_py = self.project_root / 'main.py'
        if not main_py.exists():
            self.log_error("main.py not found")
            return False
            
        try:
            with open(main_py, 'r') as f:
                content = f.read()
                
            # Check for problematic patterns
            if 'asyncio.run(' in content:
                self.log_warning("Found asyncio.run() in main.py - may cause event loop conflicts")
                
            if 'nest_asyncio' not in content and 'asyncio.run(' in content:
                self.log_warning("Consider using nest_asyncio for event loop compatibility")
                
            logger.info("✓ Event loop configuration checked")
            return True
            
        except Exception as e:
            self.log_error(f"Error checking event loop: {e}")
            return False
            
    def check_static_files(self) -> bool:
        """Check static file configuration"""
        logger.info("=== CHECKING STATIC FILES ===")
        
        static_dirs = ['static', 'frontend/dist', 'public']
        found_static = False
        
        for static_dir in static_dirs:
            static_path = self.project_root / static_dir
            if static_path.exists():
                logger.info(f"✓ Found static directory: {static_dir}")
                found_static = True
                
        if not found_static:
            self.log_warning("No static directories found - may need to build frontend")
            
        return True
        
    def run_first_pass_audit(self) -> bool:
        """Run first pass comprehensive audit"""
        logger.info("\n" + "="*50)
        logger.info("STARTING FIRST PASS AUDIT")
        logger.info("="*50)
        
        checks = [
            self.check_python_dependencies,
            self.check_environment_files,
            self.check_syntax_errors,
            self.check_event_loop_issues,
            self.check_static_files
        ]
        
        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_error(f"Check failed: {check.__name__}", str(e))
                all_passed = False
                
        logger.info(f"\nFIRST PASS AUDIT COMPLETE - {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
        
    def run_second_pass_verification(self) -> bool:
        """Run second pass verification"""
        logger.info("\n" + "="*50)
        logger.info("STARTING SECOND PASS VERIFICATION")
        logger.info("="*50)
        
        # Test server startup
        try:
            logger.info("Testing server startup...")
            result = subprocess.run([
                sys.executable, '-c',
                "from main import app; print('Server import successful')"
            ], capture_output=True, text=True, timeout=10, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✓ Server import successful")
                self.verification_results['server_import'] = True
            else:
                self.log_error("Server import failed", result.stderr)
                self.verification_results['server_import'] = False
                
        except Exception as e:
            self.log_error("Server startup test failed", str(e))
            self.verification_results['server_import'] = False
            
        # Check if all critical issues are resolved
        critical_issues = len([e for e in self.errors if 'critical' in e.get('message', '').lower()])
        
        verification_passed = (
            self.verification_results.get('server_import', False) and
            critical_issues == 0
        )
        
        logger.info(f"\nSECOND PASS VERIFICATION COMPLETE - {'PASSED' if verification_passed else 'FAILED'}")
        return verification_passed
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive debug report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'fixes_applied': len(self.fixes_applied)
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'fixes_applied': self.fixes_applied,
            'verification_results': self.verification_results
        }
        
        # Save report to file
        report_file = self.project_root / 'debug_guard_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Debug report saved to: {report_file}")
        return report
        
    def run_full_audit(self) -> bool:
        """Run complete two-pass audit system"""
        logger.info("\n" + "#"*60)
        logger.info("BASE44 DEBUG GUARD - COMPREHENSIVE AUDIT STARTING")
        logger.info("#"*60)
        
        try:
            # First pass
            first_pass_result = self.run_first_pass_audit()
            
            # Second pass
            second_pass_result = self.run_second_pass_verification()
            
            # Generate report
            report = self.generate_report()
            
            # Final assessment
            overall_success = first_pass_result and second_pass_result
            
            logger.info("\n" + "#"*60)
            logger.info(f"AUDIT COMPLETE - {'SUCCESS' if overall_success else 'FAILED'}")
            logger.info(f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}, Fixes: {len(self.fixes_applied)}")
            logger.info("#"*60)
            
            return overall_success
            
        except Exception as e:
            self.log_error("Critical failure in audit system", str(e))
            logger.error(f"CRITICAL AUDIT FAILURE: {e}")
            logger.error(traceback.format_exc())
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Base44 Debug Guard')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    guard = Base44DebugGuard(args.project_root)
    success = guard.run_full_audit()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
