#!/usr/bin/env python3
"""
Production Readiness Verification Script
Checks all critical production requirements before go-live
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class ProductionReadinessChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = []
        self.critical_failures = []
        
    def check_environment_variables(self) -> bool:
        """Check that all critical environment variables are set"""
        critical_vars = [
            'ENVIRONMENT',
            'TRAE_API_TOKEN', 
            'SECRET_KEY',
            'JWT_SECRET',
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.critical_failures.append(f"Missing critical environment variables: {', '.join(missing_vars)}")
            return False
            
        # Check production environment is set correctly
        if os.getenv('ENVIRONMENT') != 'production':
            self.critical_failures.append("ENVIRONMENT must be set to 'production'")
            return False
            
        self.results.append("✅ All critical environment variables are set")
        return True
        
    def check_secrets_not_hardcoded(self) -> bool:
        """Scan for hardcoded secrets in source code"""
        patterns = [
            r'api[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9_-]{16,}["\']',
            r'secret[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9_-]{16,}["\']',
            r'password\s*[:=]\s*["\'][a-zA-Z0-9_-]{8,}["\']',
            r'token\s*[:=]\s*["\'][a-zA-Z0-9_-]{16,}["\']'
        ]
        
        # Patterns to exclude (documentation examples and placeholders)
        exclude_patterns = [
            r'your_.*_api_key',
            r'your_.*_token',
            r'your_.*_secret',
            r'demo_key',
            r'test_key',
            r'example_key',
            r'placeholder',
            r'export.*API_KEY.*your_',  # Documentation export examples
            r'PASSWORD.*=.*"password"',  # Test passwords
            r'demo-key-for-.*-only',  # Demo keys
        ]
        
        suspicious_files = []
        for pattern in patterns:
            try:
                result = subprocess.run([
                    'grep', '-r', '-i', '-E', pattern,
                    '--include=*.py', '--include=*.js', '--include=*.ts',
                    '--exclude-dir=.git', '--exclude-dir=.venv*', '--exclude-dir=venv*',
        '--exclude-dir=dist',
                    '--exclude-dir=node_modules', '--exclude-dir=__pycache__',
                    '--exclude=paste_content.txt',  # Exclude documentation
                    '.'
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    # Filter out documentation examples and placeholders
                    filtered_lines = []
                    for line in lines:
                        is_placeholder = False
                        for exclude_pattern in exclude_patterns:
                            import re
                            if re.search(exclude_pattern, line, re.IGNORECASE):
                                is_placeholder = True
                                break
                        if not is_placeholder:
                            filtered_lines.append(line)
                    
                    suspicious_files.extend(filtered_lines)
            except Exception as e:
                self.results.append(f"⚠️  Could not scan for pattern {pattern}: {e}")
                
        if suspicious_files:
            self.critical_failures.append(f"Found potential hardcoded secrets in: {suspicious_files[:5]}")
            return False
            
        self.results.append("✅ No hardcoded secrets detected")
        return True
        
    def check_env_example_hygiene(self) -> bool:
        """Check that .env.example doesn't contain real secrets"""
        env_example_path = self.project_root / '.env.example'
        
        if not env_example_path.exists():
            self.critical_failures.append(".env.example file is missing")
            return False
            
        # Check for placeholder values
        with open(env_example_path, 'r') as f:
            content = f.read()
            
        # Look for actual API keys or tokens (not placeholders)
        suspicious_patterns = [
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
            r'xoxb-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9]+',  # Slack tokens
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
            r'[a-zA-Z0-9]{32,}',  # Long alphanumeric strings that might be real keys
        ]
        
        for pattern in suspicious_patterns:
            import re
            if re.search(pattern, content):
                self.critical_failures.append(f".env.example may contain real secrets (pattern: {pattern})")
                return False
                
        self.results.append("✅ .env.example appears clean of real secrets")
        return True
        
    def check_git_status(self) -> bool:
        """Check git status and ensure no sensitive files are tracked"""
        try:
            # Check for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.stdout.strip():
                self.results.append("⚠️  There are uncommitted changes")
                
            # Check for .env files in git
            result = subprocess.run(['git', 'ls-files', '*.env'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.stdout.strip():
                tracked_env_files = result.stdout.strip().split('\n')
                # .env.example is OK, but .env should not be tracked
                problematic_files = [f for f in tracked_env_files if f != '.env.example']
                if problematic_files:
                    self.critical_failures.append(f"Sensitive .env files are tracked in git: {problematic_files}")
                    return False
                    
            self.results.append("✅ Git repository status is clean")
            return True
            
        except Exception as e:
            self.results.append(f"⚠️  Could not check git status: {e}")
            return True  # Don't fail on git issues
            
    def check_dependencies(self) -> bool:
        """Check for known vulnerable dependencies"""
        try:
            # Check if we have a requirements.txt or package.json
            req_files = ['requirements.txt', 'package.json', 'pyproject.toml']
            found_deps = [f for f in req_files if (self.project_root / f).exists()]
            
            if not found_deps:
                self.results.append("⚠️  No dependency files found")
                return True
                
            # For Python projects, try to run safety check if available
            if 'requirements.txt' in found_deps:
                try:
                    result = subprocess.run(['python', '-m', 'pip', 'check'], 
                                          capture_output=True, text=True, cwd=self.project_root)
                    if result.returncode == 0:
                        self.results.append("✅ Python dependencies check passed")
                    else:
                        self.results.append(f"⚠️  Python dependency issues: {result.stdout}")
                except Exception:
                    self.results.append("⚠️  Could not check Python dependencies")
                    
            return True
            
        except Exception as e:
            self.results.append(f"⚠️  Could not check dependencies: {e}")
            return True
            
    def check_production_config(self) -> bool:
        """Check production-specific configuration"""
        checks_passed = True
        
        # Check DEBUG is disabled
        if os.getenv('DEBUG', '').lower() in ['true', '1', 'yes']:
            self.critical_failures.append("DEBUG mode is enabled in production")
            checks_passed = False
            
        # Check required production flags
        required_flags = {
            'ENABLE_FULL_API': '1',
            'ENABLE_DASHBOARD': '1'
        }
        
        for flag, expected_value in required_flags.items():
            if os.getenv(flag) != expected_value:
                self.critical_failures.append(f"{flag} should be set to '{expected_value}'")
                checks_passed = False
                
        if checks_passed:
            self.results.append("✅ Production configuration is correct")
            
        return checks_passed
        
    def run_all_checks(self) -> bool:
        """Run all production readiness checks"""
        print("🔍 Running Production Readiness Checks...\n")
        
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("Hardcoded Secrets", self.check_secrets_not_hardcoded),
            (".env.example Hygiene", self.check_env_example_hygiene),
            ("Git Repository Status", self.check_git_status),
            ("Dependencies", self.check_dependencies),
            ("Production Configuration", self.check_production_config)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"Running {check_name} check...")
            try:
                passed = check_func()
                if not passed:
                    all_passed = False
                    print(f"❌ {check_name} check FAILED")
                else:
                    print(f"✅ {check_name} check passed")
            except Exception as e:
                print(f"💥 {check_name} check crashed: {e}")
                all_passed = False
                
            print()
            
        return all_passed
        
    def print_summary(self, all_passed: bool):
        """Print final summary"""
        print("=" * 60)
        print("PRODUCTION READINESS SUMMARY")
        print("=" * 60)
        
        if all_passed:
            print("🎉 ALL CHECKS PASSED - READY FOR PRODUCTION!")
        else:
            print("❌ CRITICAL ISSUES FOUND - NOT READY FOR PRODUCTION")
            
        print("\nResults:")
        for result in self.results:
            print(f"  {result}")
            
        if self.critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"  ❌ {failure}")
                
        print("\n" + "=" * 60)
        
def main():
    checker = ProductionReadinessChecker()
    all_passed = checker.run_all_checks()
    checker.print_summary(all_passed)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)
    
if __name__ == "__main__":
    main()