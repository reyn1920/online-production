#!/usr / bin / env python3
"""
LIVE Production Deployment Readiness Checker

This script verifies that all components are ready for LIVE production deployment.
NO VIRTUAL ENVIRONMENTS - Production deployment only.
Automation requires explicit user authorization.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def check_file_exists(file_path, description):
    """Check if a required file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False


def check_package_json():
    """Verify package.json has required scripts"""
    try:
        with open('package.json', 'r') as f:
            package_data = json.load(f)

        required_scripts = ['build', 'lint']
        scripts = package_data.get('scripts', {})

        missing_scripts = []
        for script in required_scripts:
            if script in scripts:
                print(f"✅ npm script '{script}': {scripts[script]}")
            else:
                print(f"❌ npm script '{script}': MISSING")
                missing_scripts.append(script)

        return len(missing_scripts) == 0
    except FileNotFoundError:
        print("❌ package.json: MISSING")
        return False
    except json.JSONDecodeError:
        print("❌ package.json: INVALID JSON")
        return False


def check_git_status():
    """Check git repository status for LIVE production deployment"""
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'status', '--porcelain'],
            capture_output = True, text = True, check = True)

        if result.stdout.strip():
            print("⚠️  Git status: Uncommitted changes detected - NOT READY FOR LIVE")
            print("   Must commit all changes before LIVE production deployment")
            return False
        else:
            print("✅ Git status: Clean working directory - READY FOR LIVE PRODUCTION")
            return True

    except subprocess.CalledProcessError:
        print("❌ Git repository: Not initialized or not accessible - CANNOT GO LIVE")
        return False
    except FileNotFoundError:
        print("❌ Git: Not installed or not in PATH - CANNOT GO LIVE")
        return False


def check_github_workflow():
    """Check if GitHub Actions workflow exists"""
    workflow_path = '.github / workflows / deploy.yml'
    if check_file_exists(workflow_path, "GitHub Actions workflow"):
        try:
            with open(workflow_path, 'r') as f:
                content = f.read()
                if 'NETLIFY_AUTH_TOKEN' in content and 'NETLIFY_SITE_ID' in content:
                    print("✅ Workflow configured for Netlify deployment")
                    return True
                else:
                    print("⚠️  Workflow missing Netlify configuration")
                    return False
        except Exception as e:
            print(f"❌ Error reading workflow: {e}")
            return False
    return False


def check_netlify_config():
    """Check Netlify configuration"""
    netlify_toml = check_file_exists('netlify.toml', "Netlify configuration")

    # Check for build output directory
    dist_exists = os.path.exists('dist')
    if dist_exists:
        print("✅ Build output directory: dist/ exists")
    else:
        print("⚠️  Build output directory: dist/ not found (will be created during build)")

    return netlify_toml


def check_environment_template():
    """Check environment template file"""
    env_example = check_file_exists('.env.example', "Environment template")

    if env_example:
        try:
            with open('.env.example', 'r') as f:
                content = f.read()
                required_vars = ['JWT_SECRET', 'OPENAI_API_KEY', 'GOOGLE_API_KEY']
                missing_vars = []

                for var in required_vars:
                    if var in content:
                        print(f"✅ Environment variable template: {var}")
                    else:
                        print(f"⚠️  Environment variable template: {var} not found")
                        missing_vars.append(var)

                return len(missing_vars) == 0
        except Exception as e:
            print(f"❌ Error reading .env.example: {e}")
            return False

    return env_example


def check_ai_integrations():
    """Check AI integration files"""
    ai_files = [
        ('backend / ai_benchmark_integration.py', 'AI Benchmark Integration'),
        ('app / quality_dashboard.py', 'Quality Dashboard'),
        ('app / dashboard.py', 'Main Dashboard')
    ]

    all_exist = True
    for file_path, description in ai_files:
        if not check_file_exists(file_path, description):
            all_exist = False

    return all_exist


def generate_readiness_report(results):
    """Generate deployment readiness report"""
    report = {
        'timestamp': datetime.now().isoformat(),
            'project_root': os.getcwd(),
            'readiness_check': {
            'total_checks': len(results),
                'passed_checks': sum(1 for r in results.values() if r),
                'failed_checks': sum(1 for r in results.values() if not r),
                'success_rate': round((sum(1 for r in results.values() if r) / len(results)) * 100,
    2)
        },
            'detailed_results': results,
            'deployment_status': 'READY' if all(results.values()) else 'NOT_READY',
            'next_steps': []
    }

    # Add specific next steps based on failures
    if not results.get('github_secrets_info', True):
        report['next_steps'].append('Configure GitHub repository secrets (NETLIFY_AUTH_TOKEN,
    NETLIFY_SITE_ID)')

    if not results.get('netlify_config', True):
        report['next_steps'].append('Set up Netlify site and configuration')

    if not results.get('git_status', True):
        report['next_steps'].append('Commit and push changes to main branch')

    if report['deployment_status'] == 'READY':
        report['next_steps'] = [
            'Configure GitHub secrets (see DEPLOYMENT_SETUP_GUIDE.md)',
                'Set up Netlify site',
                'Run staging deployment test',
                'Deploy to production'
        ]

    return report


def main():
    """Main LIVE production deployment readiness check"""
    print("🚨 LIVE Production Deployment Readiness Check")
    print("NO VIRTUAL ENVIRONMENTS - PRODUCTION ONLY")
    print("=" * 60)

    # Run all checks
    results = {
        'package_json': check_package_json(),
            'git_status': check_git_status(),
            'github_workflow': check_github_workflow(),
            'netlify_config': check_netlify_config(),
            'environment_template': check_environment_template(),
            'ai_integrations': check_ai_integrations()
    }

    print("\\n" + "=" * 50)

    # Generate report
    report = generate_readiness_report(results)

    # Save report
    with open('deployment_readiness_report.json', 'w') as f:
        json.dump(report, f, indent = 2)

    # Print summary
    print(f"📊 DEPLOYMENT READINESS SUMMARY")
    print(f"Status: {report['deployment_status']}")
    print(f"Checks Passed: {report['readiness_check']['passed_checks']}/{report['readiness_check']['total_checks']}")
    print(f"Success Rate: {report['readiness_check']['success_rate']}%")

    if report['deployment_status'] == 'READY':
        print("\\n🎉 System is ready for LIVE PRODUCTION deployment!")
        print("\\n🚨 LIVE DEPLOYMENT RULES:")
        print("   • NO VIRTUAL ENVIRONMENTS")
        print("   • PRODUCTION ONLY")
        print("   • AUTOMATION REQUIRES USER AUTHORIZATION")
        print("\\n📋 Next Steps:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"   {i}. {step}")
        print("   5. EXPLICITLY AUTHORIZE automation when prompted")
    else:
        print("\\n⚠️  System needs attention before LIVE production deployment")
        print("\\n🔧 Required Actions for LIVE deployment:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"   {i}. {step}")

    print(f"\\n📄 Detailed report saved to: deployment_readiness_report.json")
    print(f"📚 See DEPLOYMENT_SETUP_GUIDE.md for detailed instructions")

    # Exit with appropriate code
    sys.exit(0 if report['deployment_status'] == 'READY' else 1)

if __name__ == '__main__':
    main()