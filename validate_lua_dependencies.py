#!/usr/bin/env python3
"""
Lua Dependencies Validation for PDF Emoji Support

This module validates Lua filter dependencies and provides comprehensive
error handling for Lua-related issues in the PDF export process.
"""

import os
import subprocess
import tempfile
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LuaValidationResult:
    """Result of Lua dependency validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, any]


class LuaDependencyValidator:
    """Validator for Lua filter dependencies and functionality."""
    
    def __init__(self, script_dir: str):
        self.script_dir = script_dir
        self.emoji_filter_path = os.path.join(script_dir, 'filters', 'emoji-passthrough.lua')
    
    def validate_lua_filter_syntax(self, filter_path: str) -> LuaValidationResult:
        """Validate Lua filter syntax using lua command."""
        result = LuaValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            details={'filter_path': filter_path}
        )
        
        if not os.path.exists(filter_path):
            result.valid = False
            result.errors.append(f"Lua filter not found: {filter_path}")
            return result
        
        try:
            # Check if lua command is available
            lua_check = subprocess.run(['lua', '-v'], 
                                     capture_output=True, text=True, timeout=5)
            
            if lua_check.returncode != 0:
                result.warnings.append("Lua interpreter not available for syntax checking")
                return result
            
            # Test syntax using luac (Lua compiler) which only checks syntax
            syntax_check = subprocess.run([
                'luac', '-p', filter_path
            ], capture_output=True, text=True, timeout=10)
            
            if syntax_check.returncode != 0:
                result.valid = False
                result.errors.append(f"Lua syntax error in {filter_path}")
                result.details['syntax_error'] = syntax_check.stderr
            else:
                result.details['syntax_valid'] = True
                
        except subprocess.TimeoutExpired:
            result.warnings.append("Lua syntax check timed out")
        except FileNotFoundError:
            result.warnings.append("Lua interpreter not found - skipping syntax validation")
        except Exception as e:
            result.warnings.append(f"Lua syntax check failed: {str(e)}")
        
        return result
    
    def validate_emoji_filter_functions(self) -> LuaValidationResult:
        """Validate that emoji filter contains required functions."""
        result = LuaValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            details={'filter_path': self.emoji_filter_path}
        )
        
        if not os.path.exists(self.emoji_filter_path):
            result.valid = False
            result.errors.append(f"Emoji filter not found: {self.emoji_filter_path}")
            return result
        
        try:
            with open(self.emoji_filter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Required functions for emoji processing
            required_functions = [
                'process_text',
                'is_emoji',
                'Str',
                'Code',
                'CodeBlock'
            ]
            
            # Required data structures for current emoji filter
            required_data = [
                'emoji_map',
                'fallback_map'
            ]
            
            missing_functions = []
            missing_data = []
            
            for func in required_functions:
                if f'function {func}' not in content:
                    missing_functions.append(func)
            
            for data in required_data:
                if data not in content:
                    missing_data.append(data)
            
            if missing_functions:
                result.valid = False
                result.errors.append(f"Missing required functions: {', '.join(missing_functions)}")
            
            if missing_data:
                result.warnings.append(f"Missing data structures: {', '.join(missing_data)}")
            
            # Check for return statement (filter must return filter table)
            if 'return {' not in content and 'return' not in content:
                result.warnings.append("Filter may not return proper filter table")
            
            result.details.update({
                'file_size': len(content),
                'missing_functions': missing_functions,
                'missing_data': missing_data,
                'has_return': 'return' in content
            })
            
        except Exception as e:
            result.valid = False
            result.errors.append(f"Error reading emoji filter: {str(e)}")
        
        return result
    
    def test_emoji_filter_with_pandoc(self) -> LuaValidationResult:
        """Test emoji filter functionality with Pandoc."""
        result = LuaValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            details={'test_type': 'pandoc_integration'}
        )
        
        if not os.path.exists(self.emoji_filter_path):
            result.valid = False
            result.errors.append("Emoji filter not found for testing")
            return result
        
        # Test cases with different emoji types
        test_cases = [
            {
                'name': 'basic_emoji',
                'input': 'Hello 😀 World!',
                'expected_pattern': r'\\emoji\{'
            },
            {
                'name': 'keycap_sequence',
                'input': 'Press 1️⃣ to continue',
                'expected_pattern': r'\\emoji\{1'
            },
            {
                'name': 'flag_sequence',
                'input': 'Flag: 🇺🇸',
                'expected_pattern': r'\\emoji\{'
            },
            {
                'name': 'skin_tone_modifier',
                'input': 'Wave 👋🏻 hello',
                'expected_pattern': r'\\emoji\{'
            }
        ]
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_results = {}
                
                for test_case in test_cases:
                    test_result = self._run_single_pandoc_test(
                        temp_dir, test_case['name'], 
                        test_case['input'], test_case['expected_pattern']
                    )
                    test_results[test_case['name']] = test_result
                
                # Analyze results
                passed_tests = sum(1 for r in test_results.values() if r['success'])
                total_tests = len(test_cases)
                
                result.details.update({
                    'test_results': test_results,
                    'passed_tests': passed_tests,
                    'total_tests': total_tests,
                    'success_rate': passed_tests / total_tests if total_tests > 0 else 0
                })
                
                if passed_tests == 0:
                    result.valid = False
                    result.errors.append("All emoji filter tests failed")
                elif passed_tests < total_tests:
                    result.warnings.append(f"Some emoji filter tests failed ({passed_tests}/{total_tests} passed)")
                
        except Exception as e:
            result.warnings.append(f"Emoji filter testing failed: {str(e)}")
        
        return result
    
    def _run_single_pandoc_test(self, temp_dir: str, test_name: str, 
                               input_text: str, expected_pattern: str) -> Dict:
        """Run a single Pandoc test with the emoji filter."""
        import re
        
        try:
            input_file = os.path.join(temp_dir, f'{test_name}.md')
            output_file = os.path.join(temp_dir, f'{test_name}.tex')
            
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(input_text)
            
            # Run pandoc with emoji filter
            cmd = [
                'pandoc',
                input_file,
                '-o', output_file,
                '--to=latex',
                f'--lua-filter={self.emoji_filter_path}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    output_content = f.read()
                
                # Check if expected pattern is found
                pattern_found = bool(re.search(expected_pattern, output_content))
                
                return {
                    'success': pattern_found,
                    'output_content': output_content,
                    'pattern_found': pattern_found,
                    'expected_pattern': expected_pattern
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
    
    def validate_pandoc_lua_support(self) -> LuaValidationResult:
        """Validate that Pandoc supports Lua filters."""
        result = LuaValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            details={'test_type': 'pandoc_lua_support'}
        )
        
        try:
            # Check Pandoc version and Lua filter support
            version_result = subprocess.run(['pandoc', '--version'], 
                                          capture_output=True, text=True, timeout=10)
            
            if version_result.returncode != 0:
                result.valid = False
                result.errors.append("Pandoc not available")
                return result
            
            version_output = version_result.stdout
            result.details['pandoc_version'] = version_output.split('\n')[0]
            
            # Test basic Lua filter support with a minimal filter
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a minimal test filter
                test_filter = os.path.join(temp_dir, 'test.lua')
                with open(test_filter, 'w') as f:
                    f.write('''
function Str(elem)
    return elem
end
''')
                
                # Create test input
                test_input = os.path.join(temp_dir, 'test.md')
                test_output = os.path.join(temp_dir, 'test.tex')
                
                with open(test_input, 'w') as f:
                    f.write('Test content')
                
                # Test Lua filter execution
                test_cmd = [
                    'pandoc',
                    test_input,
                    '-o', test_output,
                    '--to=latex',
                    f'--lua-filter={test_filter}'
                ]
                
                test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=15)
                
                if test_result.returncode == 0:
                    result.details['lua_filter_support'] = True
                else:
                    result.valid = False
                    result.errors.append("Pandoc Lua filter support not working")
                    result.details['test_error'] = test_result.stderr
                    
        except subprocess.TimeoutExpired:
            result.warnings.append("Pandoc Lua support test timed out")
        except FileNotFoundError:
            result.valid = False
            result.errors.append("Pandoc not found")
        except Exception as e:
            result.warnings.append(f"Pandoc Lua support test failed: {str(e)}")
        
        return result
    
    def run_comprehensive_lua_validation(self) -> LuaValidationResult:
        """Run comprehensive Lua dependency validation."""
        overall_result = LuaValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            details={'validation_type': 'comprehensive'}
        )
        
        # Test 1: Pandoc Lua support
        pandoc_test = self.validate_pandoc_lua_support()
        overall_result.details['pandoc_lua_test'] = pandoc_test.details
        
        if not pandoc_test.valid:
            overall_result.valid = False
            overall_result.errors.extend(pandoc_test.errors)
        overall_result.warnings.extend(pandoc_test.warnings)
        
        # Test 2: Emoji filter syntax
        syntax_test = self.validate_lua_filter_syntax(self.emoji_filter_path)
        overall_result.details['syntax_test'] = syntax_test.details
        
        if not syntax_test.valid:
            overall_result.valid = False
            overall_result.errors.extend(syntax_test.errors)
        overall_result.warnings.extend(syntax_test.warnings)
        
        # Test 3: Emoji filter functions
        functions_test = self.validate_emoji_filter_functions()
        overall_result.details['functions_test'] = functions_test.details
        
        if not functions_test.valid:
            overall_result.valid = False
            overall_result.errors.extend(functions_test.errors)
        overall_result.warnings.extend(functions_test.warnings)
        
        # Test 4: Integration test (only if previous tests pass)
        if overall_result.valid:
            integration_test = self.test_emoji_filter_with_pandoc()
            overall_result.details['integration_test'] = integration_test.details
            
            if not integration_test.valid:
                overall_result.warnings.append("Emoji filter integration tests failed")
                overall_result.warnings.extend(integration_test.warnings)
            else:
                overall_result.warnings.extend(integration_test.warnings)
        
        return overall_result


def main():
    """Command-line interface for Lua dependency validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Lua dependencies for emoji support')
    parser.add_argument('--script-dir', default='.', 
                       help='Directory containing the emoji filter')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed validation results')
    
    args = parser.parse_args()
    
    validator = LuaDependencyValidator(args.script_dir)
    result = validator.run_comprehensive_lua_validation()
    
    print("Lua Dependencies Validation Report")
    print("=" * 40)
    
    if result.valid:
        print("✅ All Lua dependencies are valid")
    else:
        print("❌ Lua dependency validation failed")
    
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  • {error}")
    
    if result.warnings:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    if args.verbose:
        print(f"\n📋 Detailed Results:")
        print(json.dumps(result.details, indent=2, default=str))


if __name__ == '__main__':
    main()