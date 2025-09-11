#!/usr/bin/env python3
"""
Production Readiness Health Check
Verifies all systems are ready for 100% automated go-live
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests


def check_api_health(url, name):
    """Check if an API endpoint is healthy"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            print(f"✅ {name}: Healthy (Status: {resp.status_code})")
            return True
        else:
            print(f"⚠️  {name}: Warning (Status: {resp.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Failed - {e}")
        return False


def check_file_exists(filepath, name):
    """Check if a critical file exists"""
    if Path(filepath).exists():
        print(f"✅ {name}: Found")
        return True
    else:
        print(f"❌ {name}: Missing")
        return False


def check_environment_config():
    """Check environment configuration"""
    print("\n🔧 Environment Configuration:")
    print("-" * 40)

    # Check .env.example exists
    env_example_ok = check_file_exists(".env.example", "Environment Template")

    # Check .gitignore protects secrets
    gitignore_ok = False
    try:
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
            if ".env" in gitignore_content:
                print("✅ Secrets Protection: .env files properly ignored")
                gitignore_ok = True
            else:
                print("❌ Secrets Protection: .env files not in .gitignore")
    except:
        print("❌ Secrets Protection: .gitignore not found")

    return env_example_ok and gitignore_ok


def check_ci_cd_pipeline():
    """Check CI/CD pipeline configuration"""
    print("\n🚀 CI/CD Pipeline:")
    print("-" * 40)

    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ GitHub Actions: Workflows directory missing")
        return False

    required_workflows = ["ci-cd.yml", "security.yml", "prod-health-watch.yml"]

    all_workflows_ok = True
    for workflow in required_workflows:
        workflow_path = workflows_dir / workflow
        if workflow_path.exists():
            print(f"✅ Workflow: {workflow}")
        else:
            print(f"❌ Workflow: {workflow} missing")
            all_workflows_ok = False

    return all_workflows_ok


def check_security_setup():
    """Check security configuration"""
    print("\n🔒 Security Setup:")
    print("-" * 40)

    # Check for security tools in requirements
    security_tools = ["bandit", "safety"]
    requirements_ok = True

    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
            for tool in security_tools:
                if tool in requirements:
                    print(f"✅ Security Tool: {tool} configured")
                else:
                    print(f"⚠️  Security Tool: {tool} not in requirements")
                    requirements_ok = False
    except:
        print("❌ Requirements: requirements.txt not found")
        requirements_ok = False

    return requirements_ok


def main():
    """Run comprehensive production readiness check"""
    print("🔍 PRODUCTION READINESS HEALTH CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Directory: {os.getcwd()}")

    # Check running services
    print("\n🌐 Service Health:")
    print("-" * 40)
    main_api_ok = check_api_health("http://localhost:8000/health", "Main API Server")
    paste_app_ok = check_api_health("http://localhost:8081", "Paste Application")

    # Check configuration
    config_ok = check_environment_config()

    # Check CI/CD
    cicd_ok = check_ci_cd_pipeline()

    # Check security
    security_ok = check_security_setup()

    # Overall assessment
    print("\n🎯 PRODUCTION READINESS SUMMARY:")
    print("=" * 50)

    all_checks = [
        ("Main API Server", main_api_ok),
        ("Paste Application", paste_app_ok),
        ("Environment Config", config_ok),
        ("CI/CD Pipeline", cicd_ok),
        ("Security Setup", security_ok),
    ]

    passed_checks = sum(1 for _, status in all_checks if status)
    total_checks = len(all_checks)

    for check_name, status in all_checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")

    print(f"\n📊 Score: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("\n🎉 SYSTEM IS 100% READY FOR AUTOMATED GO-LIVE!")
        print("\n🚀 Ready for production deployment via:")
        print("   • GitHub Actions workflow_dispatch")
        print("   • Automated CI/CD pipeline")
        print("   • Netlify production deployment")
        return 0
    else:
        print(
            f"\n⚠️  SYSTEM NEEDS ATTENTION: {total_checks - passed_checks} issues to resolve"
        )
        print("\n🔧 Next steps:")
        print("   • Fix failing checks above")
        print("   • Re-run this health check")
        print("   • Proceed with go-live when all checks pass")
        return 1


if __name__ == "__main__":
    sys.exit(main())
