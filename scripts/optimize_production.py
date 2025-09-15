#!/usr/bin/env python3
"""
Production Optimization Script
Applies performance optimizations and configurations for production deployment.
"""

import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.performance_config import (
        get_performance_config,
        get_middleware_config,
        get_caching_strategy,
        optimize_for_production
    )
    has_performance_config = True
except ImportError:
    print("Warning: Could not import performance config. Using defaults.")
    has_performance_config = False
    get_performance_config = None
    get_middleware_config = None
    get_caching_strategy = None
    optimize_for_production = None


class ProductionOptimizer:
    """Handles production optimization tasks."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.config_dir = self.project_root / "config"
        
    def optimize_build_output(self) -> bool:
        """Optimize the build output for production."""
        print("🔧 Optimizing build output...")
        
        try:
            # Check if dist directory exists
            if not self.dist_dir.exists():
                print("❌ No dist directory found. Run build first.")
                return False
            
            # Minify HTML files
            self._minify_html_files()
            
            # Optimize images
            self._optimize_images()
            
            # Generate service worker for caching
            self._generate_service_worker()
            
            # Create gzipped versions of assets
            self._create_compressed_assets()
            
            print("✅ Build output optimized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Build optimization failed: {e}")
            return False
    
    def _minify_html_files(self):
        """Minify HTML files in the dist directory."""
        html_files = list(self.dist_dir.rglob("*.html"))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                
                # Basic HTML minification
                import re
                # Remove comments
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                # Remove extra whitespace
                content = re.sub(r'>\s+<', '><', content)
                content = re.sub(r'\s+', ' ', content)
                
                html_file.write_text(content.strip(), encoding='utf-8')
                print(f"  ✓ Minified {html_file.name}")
                
            except Exception as e:
                print(f"  ⚠️  Could not minify {html_file.name}: {e}")
    
    def _optimize_images(self):
        """Optimize images in the dist directory."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        for ext in image_extensions:
            image_files = list(self.dist_dir.rglob(f"*{ext}"))
            
            for image_file in image_files:
                # For now, just report found images
                # In a real implementation, you'd use tools like imagemin
                print(f"  📷 Found image: {image_file.name}")
    
    def _generate_service_worker(self):
        """Generate a service worker for caching."""
        sw_content = '''
// Production Service Worker
const CACHE_NAME = 'app-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
'''
        
        sw_file = self.dist_dir / "sw.js"
        sw_file.write_text(sw_content, encoding='utf-8')
        print("  ✓ Generated service worker")
    
    def _create_compressed_assets(self):
        """Create gzipped versions of text assets."""
        import gzip
        
        text_extensions = ['.js', '.css', '.html', '.json', '.xml', '.txt']
        
        for ext in text_extensions:
            files = list(self.dist_dir.rglob(f"*{ext}"))
            
            for file_path in files:
                try:
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Check compression ratio
                    original_size = file_path.stat().st_size
                    compressed_size = Path(f"{file_path}.gz").stat().st_size
                    ratio = (1 - compressed_size / original_size) * 100
                    
                    print(f"  ✓ Compressed {file_path.name} ({ratio:.1f}% reduction)")
                    
                except Exception as e:
                    print(f"  ⚠️  Could not compress {file_path.name}: {e}")
    
    def setup_environment_config(self, environment: str = 'production') -> bool:
        """Setup environment-specific configuration."""
        print(f"🔧 Setting up {environment} configuration...")
        
        try:
            if has_performance_config and get_performance_config:
                # Generate performance config
                perf_config = get_performance_config(environment)
                middleware_config = get_middleware_config(perf_config)
                caching_config = get_caching_strategy()
                optimization_config = optimize_for_production()
                
                # Save configurations
                config_data = {
                    'performance': asdict(perf_config),
                    'middleware': middleware_config,
                    'caching': caching_config,
                    'optimization': optimization_config,
                    'environment': environment
                }
                
                config_file = self.config_dir / f"{environment}_config.json"
                config_file.parent.mkdir(exist_ok=True)
                
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                print(f"  ✓ Configuration saved to {config_file}")
            
            # Create environment-specific .env file
            self._create_env_file(environment)
            
            print("✅ Environment configuration completed")
            return True
            
        except Exception as e:
            print(f"❌ Environment setup failed: {e}")
            return False
    
    def _create_env_file(self, environment: str):
        """Create environment-specific .env file."""
        env_vars = {
            'NODE_ENV': environment,
            'ENVIRONMENT': environment,
            'BUILD_TIMESTAMP': str(int(time.time())),
            'COMPRESSION_ENABLED': 'true',
            'CACHE_TIMEOUT': '300',
            'RATE_LIMIT_RPM': '100',
            'STATIC_MAX_AGE': '31536000'
        }
        
        if environment == 'production':
            env_vars.update({
                'DEBUG': 'false',
                'MINIFY_ASSETS': 'true',
                'ENABLE_ANALYTICS': 'true',
                'LOG_LEVEL': 'warn'
            })
        elif environment == 'staging':
            env_vars.update({
                'DEBUG': 'false',
                'MINIFY_ASSETS': 'true',
                'ENABLE_ANALYTICS': 'false',
                'LOG_LEVEL': 'info'
            })
        
        env_file = self.project_root / f".env.{environment}"
        
        with open(env_file, 'w') as f:
            f.write(f"# {environment.upper()} Environment Configuration\n")
            f.write(f"# Generated automatically - do not edit manually\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"  ✓ Created {env_file}")
    
    def run_performance_audit(self) -> Dict[str, Any]:
        """Run a performance audit on the build output."""
        print("🔍 Running performance audit...")
        
        audit_results = {
            'timestamp': time.time(),
            'build_size': self._calculate_build_size(),
            'asset_count': self._count_assets(),
            'compression_ratio': self._calculate_compression_ratio(),
            'recommendations': []
        }
        
        # Add recommendations based on audit
        build_size = audit_results['build_size']
        compression_ratio = audit_results['compression_ratio']
        recommendations = audit_results['recommendations']
        
        if isinstance(build_size, (int, float)) and build_size > 5 * 1024 * 1024:  # 5MB
            if isinstance(recommendations, list):
                recommendations.append(
                    "Consider code splitting to reduce bundle size"
                )
        
        if isinstance(compression_ratio, (int, float)) and compression_ratio < 0.3:  # Less than 30% compression
            if isinstance(recommendations, list):
                recommendations.append(
                    "Enable gzip compression on your server"
                )
        
        # Save audit results
        audit_file = self.project_root / "performance_audit.json"
        with open(audit_file, 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        print(f"✅ Performance audit completed. Results saved to {audit_file}")
        return audit_results
    
    def _calculate_build_size(self) -> int:
        """Calculate total build size."""
        total_size = 0
        
        if self.dist_dir.exists():
            for file_path in self.dist_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        return total_size
    
    def _count_assets(self) -> Dict[str, int]:
        """Count different types of assets."""
        counts = {
            'js': 0,
            'css': 0,
            'html': 0,
            'images': 0,
            'other': 0
        }
        
        if self.dist_dir.exists():
            for file_path in self.dist_dir.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    
                    if ext == '.js':
                        counts['js'] += 1
                    elif ext == '.css':
                        counts['css'] += 1
                    elif ext == '.html':
                        counts['html'] += 1
                    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                        counts['images'] += 1
                    else:
                        counts['other'] += 1
        
        return counts
    
    def _calculate_compression_ratio(self) -> float:
        """Calculate average compression ratio."""
        total_original = 0
        total_compressed = 0
        
        if self.dist_dir.exists():
            for gz_file in self.dist_dir.rglob("*.gz"):
                original_file = Path(str(gz_file)[:-3])  # Remove .gz extension
                
                if original_file.exists():
                    total_original += original_file.stat().st_size
                    total_compressed += gz_file.stat().st_size
        
        if total_original > 0:
            return 1 - (total_compressed / total_original)
        
        return 0.0


def main():
    """Main optimization script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Optimization Script')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--skip-build', action='store_true',
                       help='Skip build optimization')
    parser.add_argument('--audit-only', action='store_true',
                       help='Run performance audit only')
    
    args = parser.parse_args()
    
    optimizer = ProductionOptimizer()
    
    print(f"🚀 Starting production optimization for {args.environment}...")
    
    success = True
    
    if not args.audit_only:
        # Setup environment configuration
        if not optimizer.setup_environment_config(args.environment):
            success = False
        
        # Optimize build output (unless skipped)
        if not args.skip_build:
            if not optimizer.optimize_build_output():
                success = False
    
    # Run performance audit
    audit_results = optimizer.run_performance_audit()
    
    # Print summary
    print("\n📊 Optimization Summary:")
    print(f"Environment: {args.environment}")
    print(f"Build Size: {audit_results['build_size'] / 1024 / 1024:.2f} MB")
    print(f"Compression Ratio: {audit_results['compression_ratio']:.1%}")
    
    if audit_results['recommendations']:
        print("\n💡 Recommendations:")
        for rec in audit_results['recommendations']:
            print(f"  • {rec}")
    
    if success:
        print("\n✅ Production optimization completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Production optimization completed with errors.")
        sys.exit(1)


if __name__ == '__main__':
    main()