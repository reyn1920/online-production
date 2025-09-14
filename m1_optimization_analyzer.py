#!/usr/bin/env python3
"""
MacBook Air M1 (16GB RAM) Optimization Analyzer
Comprehensive system analysis and optimization recommendations
"""

import json
import os
import platform
import psutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class M1OptimizationAnalyzer:
    """Comprehensive M1 MacBook Air optimization analyzer"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.is_m1 = self._detect_m1_system()
        self.recommendations = []
        
    def _detect_m1_system(self) -> bool:
        """Detect if running on M1 MacBook Air"""
        try:
            if platform.system() != "Darwin":
                return False
                
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            cpu_brand = result.stdout.strip()
            return "Apple" in cpu_brand
            
        except Exception:
            return False
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "total_memory_gb": round(memory.total / (1024**3), 2),
            "available_memory_gb": round(memory.available / (1024**3), 2),
            "memory_percent_used": memory.percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_percent_used": round((disk.used / disk.total) * 100, 1)
        }
    
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze current memory usage and provide recommendations"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        analysis = {
            "current_usage": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
                "swap_used_gb": round(swap.used / (1024**3), 2) if swap.used else 0
            },
            "status": "optimal" if memory.percent < 70 else "warning" if memory.percent < 85 else "critical",
            "recommendations": []
        }
        
        # Memory optimization recommendations
        if memory.percent > 85:
            analysis["recommendations"].extend([
                "🔴 CRITICAL: Memory usage is very high (>85%)",
                "Close unnecessary applications and browser tabs",
                "Consider restarting memory-intensive applications",
                "Enable memory compression: sudo sysctl vm.compressor_mode=4"
            ])
        elif memory.percent > 70:
            analysis["recommendations"].extend([
                "🟡 WARNING: Memory usage is elevated (>70%)",
                "Monitor memory-intensive processes",
                "Consider closing unused applications"
            ])
        else:
            analysis["recommendations"].append(
                "✅ Memory usage is optimal (<70%)"
            )
            
        if swap.used > 1024**3:  # > 1GB swap
            analysis["recommendations"].append(
                "⚠️ High swap usage detected - consider adding more RAM or closing applications"
            )
            
        return analysis
    
    def analyze_cpu_performance(self) -> Dict[str, Any]:
        """Analyze CPU performance and core utilization"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        analysis = {
            "current_usage": {
                "cpu_percent": cpu_percent,
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "frequency_mhz": cpu_freq.current if cpu_freq else "Unknown"
            },
            "m1_specific": {},
            "recommendations": []
        }
        
        if self.is_m1:
            analysis["m1_specific"] = {
                "performance_cores": 4,
                "efficiency_cores": 4,
                "total_cores": 8,
                "architecture": "ARM64"
            }
            
            analysis["recommendations"].extend([
                "✅ M1 chip detected - ARM64 optimizations available",
                "Use ARM64 native packages when possible",
                "Configure applications to use MPS (Metal Performance Shaders)"
            ])
        
        if cpu_percent > 80:
            analysis["recommendations"].extend([
                "🔴 High CPU usage detected",
                "Check for runaway processes with Activity Monitor",
                "Consider task scheduling optimization"
            ])
        elif cpu_percent > 60:
            analysis["recommendations"].append(
                "🟡 Moderate CPU usage - monitor for sustained high usage"
            )
        else:
            analysis["recommendations"].append(
                "✅ CPU usage is normal"
            )
            
        return analysis
    
    def analyze_thermal_state(self) -> Dict[str, Any]:
        """Analyze thermal state and power management"""
        analysis = {
            "thermal_state": "unknown",
            "power_adapter": "unknown",
            "recommendations": []
        }
        
        try:
            # Get thermal state
            result = subprocess.run(
                ["pmset", "-g", "therm"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "No thermal warning level" in result.stdout:
                analysis["thermal_state"] = "normal"
                analysis["recommendations"].append("✅ Thermal state is normal")
            else:
                analysis["thermal_state"] = "warning"
                analysis["recommendations"].extend([
                    "🟡 Thermal warning detected",
                    "Ensure proper ventilation",
                    "Close CPU-intensive applications",
                    "Consider using a laptop stand for better airflow"
                ])
                
        except Exception:
            analysis["recommendations"].append(
                "⚠️ Could not determine thermal state"
            )
            
        try:
            # Get power adapter info
            result = subprocess.run(
                ["pmset", "-g", "adapter"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "No adapter attached" in result.stdout:
                analysis["power_adapter"] = "battery"
                analysis["recommendations"].extend([
                    "🔋 Running on battery power",
                    "Enable Low Power Mode for extended battery life",
                    "Reduce screen brightness and close unnecessary apps"
                ])
            else:
                analysis["power_adapter"] = "connected"
                analysis["recommendations"].append(
                    "🔌 Power adapter connected - optimal performance available"
                )
                
        except Exception:
            pass
            
        return analysis
    
    def analyze_development_environment(self) -> Dict[str, Any]:
        """Analyze development environment optimization"""
        analysis = {
            "python_environment": {},
            "node_environment": {},
            "docker_status": {},
            "recommendations": []
        }
        
        # Python analysis
        analysis["python_environment"] = {
            "version": platform.python_version(),
            "executable": sys.executable,
            "architecture": platform.architecture()[0]
        }
        
        # Check for ARM64 Python
        if platform.machine() == "arm64":
            analysis["recommendations"].append(
                "✅ Running ARM64 native Python - optimal for M1"
            )
        else:
            analysis["recommendations"].append(
                "⚠️ Consider using ARM64 native Python for better M1 performance"
            )
            
        # Check Node.js
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                analysis["node_environment"]["version"] = result.stdout.strip()
                analysis["recommendations"].append(
                    "✅ Node.js detected - ensure ARM64 version for M1 optimization"
                )
        except Exception:
            analysis["recommendations"].append(
                "💡 Consider installing Node.js ARM64 for web development"
            )
            
        # Check Docker
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                analysis["docker_status"]["version"] = result.stdout.strip()
                analysis["recommendations"].extend([
                    "✅ Docker detected",
                    "Use --platform=linux/arm64 for M1-optimized containers",
                    "Enable Docker Desktop's 'Use Rosetta for x86/amd64 emulation' if needed"
                ])
        except Exception:
            analysis["recommendations"].append(
                "💡 Consider Docker Desktop for containerized development"
            )
            
        return analysis
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get comprehensive optimization recommendations"""
        recommendations = [
            "🚀 MacBook Air M1 (16GB) Optimization Recommendations:",
            "",
            "📊 SYSTEM CONFIGURATION:",
            "• Enable 'Reduce motion' in System Preferences > Accessibility",
            "• Set Energy Saver to 'Automatic graphics switching'",
            "• Use Safari instead of Chrome when possible (more energy efficient)",
            "",
            "💾 MEMORY OPTIMIZATION:",
            "• Close unused browser tabs and applications",
            "• Use Activity Monitor to identify memory-hungry processes",
            "• Enable memory compression: sudo sysctl vm.compressor_mode=4",
            "• Consider using lightweight alternatives for heavy applications",
            "",
            "⚡ DEVELOPMENT OPTIMIZATION:",
            "• Use ARM64 native packages and dependencies",
            "• Configure IDEs to use MPS acceleration when available",
            "• Set PYTORCH_ENABLE_MPS_FALLBACK=1 for PyTorch",
            "• Use Homebrew ARM64 packages: /opt/homebrew/bin/brew",
            "",
            "🔧 FASTAPI/UVICORN OPTIMIZATION:",
            "• Use 2-4 workers for optimal M1 performance",
            "• Enable uvloop: pip install uvloop",
            "• Set worker_class='uvicorn.workers.UvicornWorker'",
            "• Configure max_requests=1000 for memory management",
            "",
            "🐳 DOCKER OPTIMIZATION:",
            "• Use ARM64 base images: FROM --platform=linux/arm64",
            "• Enable BuildKit: export DOCKER_BUILDKIT=1",
            "• Use multi-stage builds to reduce image size",
            "",
            "🔋 BATTERY OPTIMIZATION:",
            "• Enable Low Power Mode when on battery",
            "• Reduce screen brightness",
            "• Close unnecessary background applications",
            "• Use Terminal instead of resource-heavy terminals"
        ]
        
        return recommendations
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive system analysis"""
        print("🔍 Running MacBook Air M1 Optimization Analysis...\n")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.system_info,
            "is_m1_system": self.is_m1,
            "memory_analysis": self.analyze_memory_usage(),
            "cpu_analysis": self.analyze_cpu_performance(),
            "thermal_analysis": self.analyze_thermal_state(),
            "development_analysis": self.analyze_development_environment(),
            "optimization_recommendations": self.get_optimization_recommendations()
        }
        
        return analysis_results
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print formatted analysis report"""
        print("="*80)
        print("🍎 MacBook Air M1 (16GB) Optimization Analysis Report")
        print("="*80)
        print(f"📅 Analysis Date: {analysis['timestamp']}")
        print(f"🖥️  M1 System Detected: {'✅ Yes' if analysis['is_m1_system'] else '❌ No'}")
        print()
        
        # System Info
        print("📋 SYSTEM INFORMATION:")
        sys_info = analysis['system_info']
        print(f"   • Platform: {sys_info['platform']}")
        print(f"   • Architecture: {sys_info['architecture']}")
        print(f"   • CPU Cores: {sys_info['cpu_count']} physical, {sys_info['cpu_count_logical']} logical")
        print(f"   • Total Memory: {sys_info['total_memory_gb']} GB")
        print(f"   • Available Memory: {sys_info['available_memory_gb']} GB")
        print(f"   • Disk Space: {sys_info['disk_free_gb']} GB free of {sys_info['disk_total_gb']} GB")
        print()
        
        # Memory Analysis
        print("💾 MEMORY ANALYSIS:")
        mem_analysis = analysis['memory_analysis']
        status_emoji = "✅" if mem_analysis['status'] == 'optimal' else "🟡" if mem_analysis['status'] == 'warning' else "🔴"
        print(f"   Status: {status_emoji} {mem_analysis['status'].upper()}")
        print(f"   Usage: {mem_analysis['current_usage']['used_gb']:.1f} GB / {mem_analysis['current_usage']['total_gb']:.1f} GB ({mem_analysis['current_usage']['percent_used']:.1f}%)")
        if mem_analysis['current_usage']['swap_used_gb'] > 0:
            print(f"   Swap: {mem_analysis['current_usage']['swap_used_gb']:.1f} GB")
        for rec in mem_analysis['recommendations']:
            print(f"   {rec}")
        print()
        
        # CPU Analysis
        print("⚡ CPU ANALYSIS:")
        cpu_analysis = analysis['cpu_analysis']
        print(f"   Current Usage: {cpu_analysis['current_usage']['cpu_percent']:.1f}%")
        if analysis['is_m1_system']:
            m1_info = cpu_analysis['m1_specific']
            print(f"   M1 Configuration: {m1_info['performance_cores']} P-cores + {m1_info['efficiency_cores']} E-cores")
        for rec in cpu_analysis['recommendations']:
            print(f"   {rec}")
        print()
        
        # Thermal Analysis
        print("🌡️  THERMAL & POWER ANALYSIS:")
        thermal_analysis = analysis['thermal_analysis']
        print(f"   Thermal State: {thermal_analysis['thermal_state']}")
        print(f"   Power Source: {thermal_analysis['power_adapter']}")
        for rec in thermal_analysis['recommendations']:
            print(f"   {rec}")
        print()
        
        # Development Environment
        print("🛠️  DEVELOPMENT ENVIRONMENT:")
        dev_analysis = analysis['development_analysis']
        print(f"   Python: {dev_analysis['python_environment']['version']} ({dev_analysis['python_environment']['architecture']})")
        if 'version' in dev_analysis['node_environment']:
            print(f"   Node.js: {dev_analysis['node_environment']['version']}")
        if 'version' in dev_analysis['docker_status']:
            print(f"   Docker: {dev_analysis['docker_status']['version']}")
        for rec in dev_analysis['recommendations']:
            print(f"   {rec}")
        print()
        
        # Optimization Recommendations
        print("🚀 OPTIMIZATION RECOMMENDATIONS:")
        for rec in analysis['optimization_recommendations']:
            print(f"   {rec}")
        print()
        
        print("="*80)
        print("💡 For more detailed optimization, run the M1 Performance Optimizer:")
        print("   python backend/m1_optimizer.py")
        print("="*80)

def main():
    """Main function to run the analysis"""
    analyzer = M1OptimizationAnalyzer()
    
    try:
        # Run comprehensive analysis
        analysis = analyzer.run_comprehensive_analysis()
        
        # Print the report
        analyzer.print_analysis_report(analysis)
        
        # Save results to file
        output_file = Path("m1_optimization_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"📄 Detailed analysis saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())