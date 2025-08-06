#!/usr/bin/env python3
"""
Comprehensive Error Handling and Diagnostics for PDF Emoji Support

This module provides comprehensive error handling, validation, and diagnostic
capabilities for the PDF book exporter's emoji support functionality.

Features:
- Font availability checking with clear error messages
- Graceful fallback when LuaLaTeX is unavailable
- Diagnostic information for troubleshooting emoji rendering issues
- Validation for emoji filter and Lua dependencies
"""

import os
import subprocess
import sys
import platform
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import tempfile


@dataclass
class DiagnosticResult:
    """Container for diagnostic test results."""
    name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class EmojiSupportValidation:
    """Container for emoji support validation results."""
    valid: bool = True
    engine: str = 'lualatex'  # Default to LuaLaTeX for better font compatibility
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    emoji_fonts: Dict[str, Any] = field(default_factory=dict)
    diagnostics: List[DiagnosticResult] = field(default_factory=list)
    system_info: Dict[str, str] = field(default_factory=dict)


class EmojiDiagnostics:
    """Comprehensive diagnostics and error handling for emoji support."""
    
    def __init__(self, script_dir: str = None):
        """Initialize diagnostics with script directory path."""
        self.script_dir = script_dir or os.path.dirname(__file__)
        self.system_info = self._collect_system_info()
    
    def _collect_system_info(self) -> Dict[str, str]:
        """Collect basic system information for diagnostics."""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
        }
        
        # Add LaTeX distribution info if available
        try:
            result = subprocess.run(['tex', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                first_line = result.stdout.split('\n')[0]
                info['tex_distribution'] = first_line.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            info['tex_distribution'] = 'Not detected'
        
        return info
    
    def check_lualatex_availability(self) -> DiagnosticResult:
        """Check if LuaLaTeX engine is available and functional."""
        try:
            # Test basic LuaLaTeX availability
            result = subprocess.run(['lualatex', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                
                # Test if LuaLaTeX can actually compile a simple document
                test_result = self._test_lualatex_compilation()
                
                if test_result['success']:
                    return DiagnosticResult(
                        name="LuaLaTeX Engine",
                        status="pass",
                        message=f"LuaLaTeX is available and functional: {version_info}",
                        details={'version': version_info, 'compilation_test': 'passed'}
                    )
                else:
                    return DiagnosticResult(
                        name="LuaLaTeX Engine",
                        status="warning",
                        message=f"LuaLaTeX is available but compilation test failed: {version_info}",
                        details={'version': version_info, 'compilation_error': test_result['error']},
                        suggestions=[
                            "Check LaTeX package installation",
                            "Verify LaTeX distribution is complete",
                            "Try running 'tlmgr update --self && tlmgr update --all'"
                        ]
                    )
            else:
                return DiagnosticResult(
                    name="LuaLaTeX Engine",
                    status="fail",
                    message="LuaLaTeX command failed to execute",
                    details={'stderr': result.stderr},
                    suggestions=[
                        "Install a LaTeX distribution (TeX Live or MacTeX)",
                        "Ensure LaTeX binaries are in your PATH",
                        "On macOS: brew install --cask mactex",
                        "On Ubuntu/Debian: sudo apt-get install texlive-full",
                        "On Windows: Install MiKTeX or TeX Live"
                    ]
                )
                
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                name="LuaLaTeX Engine",
                status="fail",
                message="LuaLaTeX command timed out",
                suggestions=["Check if LaTeX installation is corrupted"]
            )
        except FileNotFoundError:
            return DiagnosticResult(
                name="LuaLaTeX Engine",
                status="fail",
                message="LuaLaTeX not found in PATH",
                suggestions=[
                    "Install a LaTeX distribution that includes LuaLaTeX",
                    "On macOS: brew install --cask mactex",
                    "On Ubuntu/Debian: sudo apt-get install texlive-luatex",
                    "On Windows: Install MiKTeX or TeX Live",
                    "Ensure LaTeX binaries are added to your system PATH"
                ]
            )
    
    def _test_lualatex_compilation(self) -> Dict[str, Any]:
        """Test LuaLaTeX compilation with a minimal document."""
        test_document = r"""
\documentclass{article}
\usepackage{luatexja-fontspec}
\defaultfontfeatures{Renderer=HarfBuzz}
\begin{document}
Test document for LuaLaTeX compilation.
\end{document}
"""
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tex_file = os.path.join(temp_dir, 'test.tex')
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(test_document)
                
                result = subprocess.run([
                    'lualatex', 
                    '-interaction=nonstopmode',
                    '-output-directory=' + temp_dir,
                    tex_file
                ], capture_output=True, text=True, timeout=30, cwd=temp_dir)
                
                pdf_file = os.path.join(temp_dir, 'test.pdf')
                success = result.returncode == 0 and os.path.exists(pdf_file)
                
                return {
                    'success': success,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'error': result.stderr if not success else None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_emoji_fonts(self) -> DiagnosticResult:
        """Check for available emoji fonts with detailed analysis."""
        try:
            # Get list of all available fonts
            result = subprocess.run(['fc-list', ':', 'family'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return DiagnosticResult(
                    name="Font Detection",
                    status="warning",
                    message="fc-list command failed, using platform defaults",
                    suggestions=["Install fontconfig package for better font detection"]
                )
            
            available_fonts = result.stdout.split('\n')
            
            # Priority-based emoji font list
            emoji_font_priorities = [
                ('Apple Color Emoji', 'macOS default emoji font'),
                ('Noto Color Emoji', 'Google/Linux emoji font'),
                ('Segoe UI Emoji', 'Windows emoji font'),
                ('Arial Unicode MS', 'Fallback with basic emoji support'),
                ('Symbola', 'Unicode symbol font'),
                ('DejaVu Sans', 'Universal fallback')
            ]
            
            detected_fonts = []
            font_details = {}
            
            for font_name, description in emoji_font_priorities:
                if any(font_name in line for line in available_fonts):
                    detected_fonts.append(font_name)
                    font_details[font_name] = {
                        'description': description,
                        'available': True
                    }
                else:
                    font_details[font_name] = {
                        'description': description,
                        'available': False
                    }
            
            if detected_fonts:
                return DiagnosticResult(
                    name="Emoji Fonts",
                    status="pass",
                    message=f"Found {len(detected_fonts)} emoji font(s): {', '.join(detected_fonts)}",
                    details={
                        'detected_fonts': detected_fonts,
                        'primary_font': detected_fonts[0],
                        'font_details': font_details,
                        'total_system_fonts': len([f for f in available_fonts if f.strip()])
                    }
                )
            else:
                return DiagnosticResult(
                    name="Emoji Fonts",
                    status="warning",
                    message="No dedicated emoji fonts detected",
                    details={'font_details': font_details},
                    suggestions=self._get_font_installation_suggestions()
                )
                
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                name="Emoji Fonts",
                status="warning",
                message="Font detection timed out",
                suggestions=["Check fontconfig installation"]
            )
        except FileNotFoundError:
            return DiagnosticResult(
                name="Emoji Fonts",
                status="warning",
                message="fc-list command not found, using platform defaults",
                details={'platform_defaults': self._get_platform_default_fonts()},
                suggestions=["Install fontconfig for better font detection"]
            )
    
    def _get_font_installation_suggestions(self) -> List[str]:
        """Get platform-specific font installation suggestions."""
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            return [
                "macOS should include Apple Color Emoji by default",
                "Try: brew install --cask font-noto-color-emoji",
                "Check System Preferences > Fonts for available emoji fonts"
            ]
        elif system == 'Linux':
            return [
                "Install Noto Color Emoji: sudo apt-get install fonts-noto-color-emoji",
                "Or on Fedora: sudo dnf install google-noto-emoji-color-fonts",
                "Refresh font cache: sudo fc-cache -fv"
            ]
        elif system == 'Windows':
            return [
                "Windows should include Segoe UI Emoji by default",
                "Install Noto Color Emoji from Google Fonts",
                "Check Windows Settings > Personalization > Fonts"
            ]
        else:
            return [
                "Install Noto Color Emoji fonts for your distribution",
                "Check your package manager for emoji font packages"
            ]
    
    def _get_platform_default_fonts(self) -> List[str]:
        """Get expected default fonts for the current platform."""
        system = platform.system()
        
        defaults = {
            'Darwin': ['Apple Color Emoji', 'PingFang SC', 'Menlo'],
            'Linux': ['Noto Color Emoji', 'DejaVu Sans', 'Liberation Sans'],
            'Windows': ['Segoe UI Emoji', 'Arial', 'Times New Roman']
        }
        
        return defaults.get(system, ['DejaVu Sans', 'Liberation Sans'])
    
    def check_emoji_filter(self) -> DiagnosticResult:
        """Check emoji filter availability and functionality with comprehensive validation."""
        emoji_filter_path = os.path.join(self.script_dir, 'filters', 'emoji-passthrough.lua')
        
        if not os.path.exists(emoji_filter_path):
            return DiagnosticResult(
                name="Emoji Filter",
                status="fail",
                message=f"Emoji filter not found at {emoji_filter_path}",
                suggestions=[
                    "Ensure filters/emoji-passthrough.lua exists in the export script directory",
                    "Check if the file was accidentally deleted or moved",
                    "Verify file permissions allow reading"
                ]
            )
        
        # Use comprehensive Lua validation
        try:
            from validate_lua_dependencies import LuaDependencyValidator
            
            validator = LuaDependencyValidator(self.script_dir)
            lua_result = validator.run_comprehensive_lua_validation()
            
            if lua_result.valid:
                status = "pass"
                message = "Emoji filter is available and fully functional"
                suggestions = []
            elif lua_result.errors:
                status = "fail"
                message = f"Emoji filter has critical issues: {'; '.join(lua_result.errors[:2])}"
                suggestions = [
                    "Check filters/emoji-passthrough.lua syntax and completeness",
                    "Verify Pandoc Lua filter support",
                    "Ensure all required functions are present"
                ]
            else:
                status = "warning"
                message = f"Emoji filter has minor issues: {'; '.join(lua_result.warnings[:2])}"
                suggestions = [
                    "Consider updating filters/emoji-passthrough.lua",
                    "Check for missing optional features"
                ]
            
            return DiagnosticResult(
                name="Emoji Filter",
                status=status,
                message=message,
                details={
                    'file_path': emoji_filter_path,
                    'lua_validation': lua_result.details,
                    'errors': lua_result.errors,
                    'warnings': lua_result.warnings
                },
                suggestions=suggestions
            )
            
        except ImportError:
            # Fallback to basic validation if comprehensive validator not available
            return self._basic_emoji_filter_check(emoji_filter_path)
        except Exception as e:
            return DiagnosticResult(
                name="Emoji Filter",
                status="warning",
                message=f"Comprehensive validation failed, using basic check: {str(e)}",
                details={'validation_error': str(e)},
                suggestions=["Check validate_lua_dependencies.py availability"]
            )
    
    def _basic_emoji_filter_check(self, emoji_filter_path: str) -> DiagnosticResult:
        """Basic emoji filter check (fallback method)."""
        try:
            with open(emoji_filter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic validation - check for key functions
            required_functions = ['is_emoji', 'wrap_emoji', 'parse_emoji_sequence']
            missing_functions = []
            
            for func in required_functions:
                if f'function {func}' not in content:
                    missing_functions.append(func)
            
            if missing_functions:
                return DiagnosticResult(
                    name="Emoji Filter",
                    status="warning",
                    message=f"Emoji filter exists but may be incomplete",
                    details={
                        'file_size': len(content),
                        'missing_functions': missing_functions
                    },
                    suggestions=[
                        "Check if filters/emoji-passthrough.lua is the correct version",
                        "Consider regenerating the emoji filter file"
                    ]
                )
            
            # Test the filter with Pandoc if available
            pandoc_test = self._test_emoji_filter_with_pandoc(emoji_filter_path)
            
            return DiagnosticResult(
                name="Emoji Filter",
                status="pass",
                message="Emoji filter is available and appears functional",
                details={
                    'file_path': emoji_filter_path,
                    'file_size': len(content),
                    'pandoc_test': pandoc_test
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                name="Emoji Filter",
                status="fail",
                message=f"Error reading emoji filter: {str(e)}",
                suggestions=[
                    "Check file permissions",
                    "Verify file is not corrupted",
                    "Try regenerating the emoji filter file"
                ]
            )
    
    def _test_emoji_filter_with_pandoc(self, filter_path: str) -> Dict[str, Any]:
        """Test emoji filter functionality with Pandoc."""
        try:
            # Create a simple test document with emoji
            test_content = "Hello 😀 World! 🎉"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                input_file = os.path.join(temp_dir, 'test.md')
                output_file = os.path.join(temp_dir, 'test.tex')
                
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                
                # Run pandoc with the emoji filter
                result = subprocess.run([
                    'pandoc',
                    input_file,
                    '-o', output_file,
                    '--to=latex',
                    f'--lua-filter={filter_path}'
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output_content = f.read()
                    
                    # Check if emoji were processed (should contain \emoji{} commands)
                    emoji_processed = '\\emoji{' in output_content
                    
                    return {
                        'success': True,
                        'emoji_processed': emoji_processed,
                        'output_sample': output_content[:200] + '...' if len(output_content) > 200 else output_content
                    }
                else:
                    return {
                        'success': False,
                        'error': result.stderr,
                        'returncode': result.returncode
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_pandoc_availability(self) -> DiagnosticResult:
        """Check Pandoc availability and version."""
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                
                # Extract version number for compatibility checking
                import re
                version_match = re.search(r'pandoc (\d+)\.(\d+)(?:\.(\d+))?', version_line)
                
                if version_match:
                    major, minor, patch = version_match.groups()
                    version_tuple = (int(major), int(minor), int(patch) if patch else 0)
                    
                    # Check if version supports required features
                    min_version = (2, 10, 0)  # Minimum version for good Lua filter support
                    
                    if version_tuple >= min_version:
                        status = "pass"
                        message = f"Pandoc is available and compatible: {version_line}"
                    else:
                        status = "warning"
                        message = f"Pandoc version may be too old: {version_line}"
                        
                    return DiagnosticResult(
                        name="Pandoc",
                        status=status,
                        message=message,
                        details={
                            'version': version_line,
                            'version_tuple': version_tuple,
                            'min_required': min_version
                        },
                        suggestions=["Consider updating Pandoc to the latest version"] if status == "warning" else []
                    )
                else:
                    return DiagnosticResult(
                        name="Pandoc",
                        status="warning",
                        message=f"Could not parse Pandoc version: {version_line}",
                        details={'version_output': result.stdout}
                    )
            else:
                return DiagnosticResult(
                    name="Pandoc",
                    status="fail",
                    message="Pandoc command failed",
                    details={'stderr': result.stderr},
                    suggestions=[
                        "Install Pandoc from https://pandoc.org/installing.html",
                        "On macOS: brew install pandoc",
                        "On Ubuntu/Debian: sudo apt-get install pandoc",
                        "On Windows: Download from GitHub releases"
                    ]
                )
                
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                name="Pandoc",
                status="fail",
                message="Pandoc command timed out"
            )
        except FileNotFoundError:
            return DiagnosticResult(
                name="Pandoc",
                status="fail",
                message="Pandoc not found in PATH",
                suggestions=[
                    "Install Pandoc from https://pandoc.org/installing.html",
                    "Ensure Pandoc is added to your system PATH"
                ]
            )
    
    def check_latex_packages(self) -> DiagnosticResult:
        """Check for required LaTeX packages for emoji support."""
        required_packages = [
            ('luatexja-fontspec', 'Japanese font support for LuaLaTeX'),
            ('fontspec', 'Font selection for XeLaTeX and LuaLaTeX'),
            ('graphicx', 'Graphics inclusion'),
            ('hyperref', 'PDF bookmarks and links'),
            ('xcolor', 'Color support'),
            ('geometry', 'Page layout'),
        ]
        
        missing_packages = []
        available_packages = []
        
        for package, description in required_packages:
            if self._check_latex_package(package):
                available_packages.append((package, description))
            else:
                missing_packages.append((package, description))
        
        if not missing_packages:
            return DiagnosticResult(
                name="LaTeX Packages",
                status="pass",
                message=f"All {len(required_packages)} required LaTeX packages are available",
                details={'available_packages': [pkg for pkg, _ in available_packages]}
            )
        elif len(missing_packages) < len(required_packages):
            return DiagnosticResult(
                name="LaTeX Packages",
                status="warning",
                message=f"{len(missing_packages)} LaTeX packages are missing",
                details={
                    'missing_packages': [pkg for pkg, _ in missing_packages],
                    'available_packages': [pkg for pkg, _ in available_packages]
                },
                suggestions=[
                    f"Install missing packages: tlmgr install {' '.join(pkg for pkg, _ in missing_packages)}",
                    "Or install full LaTeX distribution: texlive-full"
                ]
            )
        else:
            return DiagnosticResult(
                name="LaTeX Packages",
                status="fail",
                message="Most or all required LaTeX packages are missing",
                details={'missing_packages': [pkg for pkg, _ in missing_packages]},
                suggestions=[
                    "Install a complete LaTeX distribution (TeX Live or MacTeX)",
                    "Run: tlmgr update --self && tlmgr update --all",
                    "Consider installing texlive-full package"
                ]
            )
    
    def _check_latex_package(self, package_name: str) -> bool:
        """Check if a specific LaTeX package is available."""
        test_document = f"""
\\documentclass{{article}}
\\usepackage{{{package_name}}}
\\begin{{document}}
Test
\\end{{document}}
"""
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tex_file = os.path.join(temp_dir, 'test.tex')
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(test_document)
                
                # Try with lualatex first, then xelatex
                for engine in ['lualatex', 'xelatex']:
                    try:
                        result = subprocess.run([
                            engine,
                            '-interaction=nonstopmode',
                            '-output-directory=' + temp_dir,
                            tex_file
                        ], capture_output=True, text=True, timeout=15, cwd=temp_dir)
                        
                        if result.returncode == 0:
                            return True
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                return False
                
        except Exception:
            return False
    
    def run_comprehensive_diagnostics(self, emoji_enabled: bool = True) -> EmojiSupportValidation:
        """Run comprehensive diagnostics for emoji support."""
        validation = EmojiSupportValidation()
        validation.system_info = self.system_info
        
        # Core system checks
        pandoc_check = self.check_pandoc_availability()
        validation.diagnostics.append(pandoc_check)
        
        if pandoc_check.status == 'fail':
            validation.valid = False
            validation.errors.append("Pandoc is required but not available")
        
        # Engine-specific checks - always check LuaLaTeX since it's now our default
        validation.engine = 'lualatex'  # Use LuaLaTeX as default engine
        lualatex_check = self.check_lualatex_availability()
        validation.diagnostics.append(lualatex_check)
        
        if lualatex_check.status == 'fail':
            validation.valid = False
            if emoji_enabled:
                validation.errors.append("LuaLaTeX is required for emoji support but not available")
            else:
                validation.errors.append("LuaLaTeX is the default engine but not available")
        elif lualatex_check.status == 'warning':
            if emoji_enabled:
                validation.warnings.append("LuaLaTeX has issues that may affect emoji rendering")
            else:
                validation.warnings.append("LuaLaTeX has issues that may affect PDF generation")
        
        # Font checks
        font_check = self.check_emoji_fonts()
        validation.diagnostics.append(font_check)
        validation.emoji_fonts = font_check.details
        
        if font_check.status == 'warning':
            validation.warnings.append("Limited emoji font support detected")
        
        # Filter checks
        if emoji_enabled:
            filter_check = self.check_emoji_filter()
            validation.diagnostics.append(filter_check)
            
            if filter_check.status == 'fail':
                validation.warnings.append("Emoji filter not available - emoji processing will be limited")
            elif filter_check.status == 'warning':
                validation.warnings.append("Emoji filter may have issues")
        
        # LaTeX package checks
        package_check = self.check_latex_packages()
        validation.diagnostics.append(package_check)
        
        if package_check.status == 'fail':
            validation.valid = False
            validation.errors.append("Required LaTeX packages are missing")
        elif package_check.status == 'warning':
            validation.warnings.append("Some LaTeX packages are missing")
        
        return validation
    
    def print_diagnostic_report(self, validation: EmojiSupportValidation, verbose: bool = False):
        """Print a formatted diagnostic report."""
        print("\n" + "="*60)
        print("PDF EMOJI SUPPORT DIAGNOSTIC REPORT")
        print("="*60)
        
        # System information
        print(f"\nSystem Information:")
        for key, value in validation.system_info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Overall status
        print(f"\nOverall Status: {'✅ VALID' if validation.valid else '❌ INVALID'}")
        print(f"Recommended Engine: {validation.engine.upper()}")
        
        # Diagnostic results
        print(f"\nDiagnostic Results:")
        for diag in validation.diagnostics:
            status_icon = {'pass': '✅', 'warning': '⚠️', 'fail': '❌'}[diag.status]
            print(f"  {status_icon} {diag.name}: {diag.message}")
            
            if verbose and diag.suggestions:
                for suggestion in diag.suggestions:
                    print(f"    💡 {suggestion}")
        
        # Errors and warnings
        if validation.errors:
            print(f"\n❌ Errors ({len(validation.errors)}):")
            for error in validation.errors:
                print(f"  • {error}")
        
        if validation.warnings:
            print(f"\n⚠️  Warnings ({len(validation.warnings)}):")
            for warning in validation.warnings:
                print(f"  • {warning}")
        
        # Emoji font information
        if validation.emoji_fonts and 'detected_fonts' in validation.emoji_fonts:
            print(f"\n🎨 Emoji Fonts:")
            detected = validation.emoji_fonts['detected_fonts']
            if detected:
                print(f"  Primary: {detected[0]}")
                if len(detected) > 1:
                    print(f"  Fallbacks: {', '.join(detected[1:])}")
            else:
                print("  No dedicated emoji fonts detected")
        
        print("\n" + "="*60)
    
    def generate_troubleshooting_guide(self, validation: EmojiSupportValidation) -> str:
        """Generate a troubleshooting guide based on diagnostic results."""
        guide = []
        guide.append("# Emoji Support Troubleshooting Guide\n")
        
        if not validation.valid:
            guide.append("## Critical Issues\n")
            for error in validation.errors:
                guide.append(f"- **{error}**\n")
            
            # Find relevant suggestions
            for diag in validation.diagnostics:
                if diag.status == 'fail' and diag.suggestions:
                    guide.append(f"\n### {diag.name} Solutions:\n")
                    for suggestion in diag.suggestions:
                        guide.append(f"- {suggestion}\n")
        
        if validation.warnings:
            guide.append("\n## Warnings and Recommendations\n")
            for warning in validation.warnings:
                guide.append(f"- {warning}\n")
            
            # Find relevant suggestions
            for diag in validation.diagnostics:
                if diag.status == 'warning' and diag.suggestions:
                    guide.append(f"\n### {diag.name} Improvements:\n")
                    for suggestion in diag.suggestions:
                        guide.append(f"- {suggestion}\n")
        
        # Platform-specific guidance
        system = validation.system_info.get('platform', 'Unknown')
        guide.append(f"\n## Platform-Specific Guidance ({system})\n")
        
        if system == 'Darwin':  # macOS
            guide.extend([
                "- Install MacTeX: `brew install --cask mactex`\n",
                "- Install Pandoc: `brew install pandoc`\n",
                "- Apple Color Emoji should be available by default\n",
                "- Additional fonts: `brew install --cask font-noto-color-emoji`\n"
            ])
        elif system == 'Linux':
            guide.extend([
                "- Install TeX Live: `sudo apt-get install texlive-full`\n",
                "- Install Pandoc: `sudo apt-get install pandoc`\n",
                "- Install emoji fonts: `sudo apt-get install fonts-noto-color-emoji`\n",
                "- Refresh font cache: `sudo fc-cache -fv`\n"
            ])
        elif system == 'Windows':
            guide.extend([
                "- Install MiKTeX or TeX Live from official websites\n",
                "- Install Pandoc from GitHub releases\n",
                "- Segoe UI Emoji should be available by default\n",
                "- Ensure LaTeX and Pandoc are in system PATH\n"
            ])
        
        guide.append("\n## Testing Your Setup\n")
        guide.append("After making changes, test with:\n")
        guide.append("```bash\n")
        guide.append("python cli.py --emoji --diagnostics your_book_directory\n")
        guide.append("```\n")
        
        return "".join(guide)


def main():
    """Command-line interface for diagnostics."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Emoji support diagnostics')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed diagnostic information')
    parser.add_argument('--emoji', action='store_true', default=True,
                       help='Test emoji support (default: True)')
    parser.add_argument('--generate-guide', action='store_true',
                       help='Generate troubleshooting guide')
    parser.add_argument('--output', '-o', help='Output file for troubleshooting guide')
    
    args = parser.parse_args()
    
    # Run diagnostics
    diagnostics = EmojiDiagnostics()
    validation = diagnostics.run_comprehensive_diagnostics(args.emoji)
    
    # Print report
    diagnostics.print_diagnostic_report(validation, args.verbose)
    
    # Generate troubleshooting guide if requested
    if args.generate_guide:
        guide = diagnostics.generate_troubleshooting_guide(validation)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(guide)
            print(f"\nTroubleshooting guide written to: {args.output}")
        else:
            print("\n" + "="*60)
            print("TROUBLESHOOTING GUIDE")
            print("="*60)
            print(guide)


if __name__ == '__main__':
    main()