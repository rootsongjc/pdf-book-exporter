import subprocess

def detect_emoji_fonts():
    detected_fonts = {
        'primary': None,
        'fallbacks': [],
        'available': []
    }
    emoji_font_priorities = [
        'Apple Color Emoji',
        'Noto Color Emoji',
        'Segoe UI Emoji',
        'Arial Unicode MS',
        'Symbola',
        'DejaVu Sans'
    ]
    try:
        result = subprocess.run(['fc-list', ':', 'family'], 
                              capture_output=True, text=True, check=True)
        available_fonts = result.stdout.split('\n')
        for font_name in emoji_font_priorities:
            if any(font_name in line for line in available_fonts):
                detected_fonts['available'].append(font_name)
                if detected_fonts['primary'] is None:
                    detected_fonts['primary'] = font_name
                else:
                    detected_fonts['fallbacks'].append(font_name)
        if not detected_fonts['available']:
            detected_fonts['primary'] = 'Source Han Sans SC'
            detected_fonts['available'].append('Source Han Sans SC')
    except (subprocess.CalledProcessError, FileNotFoundError):
        detected_fonts['primary'] = 'Apple Color Emoji'
        detected_fonts['available'] = ['Apple Color Emoji', 'Noto Color Emoji', 'Segoe UI Emoji']
        detected_fonts['fallbacks'] = ['Noto Color Emoji', 'Segoe UI Emoji']
    return detected_fonts

def generate_emoji_font_config(emoji_fonts_info):
    if not emoji_fonts_info['available']:
        return "% No emoji fonts detected\n\\let\\emojifont\\rmfamily\n"
    latex_config = []
    latex_config.append("% Enhanced emoji font detection and configuration")
    primary_font = emoji_fonts_info['primary']
    fallback_fonts = emoji_fonts_info['fallbacks']
    latex_config.append(f"\\IfFontExistsTF{{{primary_font}}}{{")
    latex_config.append(f"  \\newfontfamily\\emojifont{{{primary_font}}}[Renderer=HarfBuzz]")
    latex_config.append(f"  \\typeout{{Using {primary_font} for emoji rendering}}")
    latex_config.append("}{")
    current_indent = "  "
    for i, fallback_font in enumerate(fallback_fonts):
        latex_config.append(f"{current_indent}\\IfFontExistsTF{{{fallback_font}}}{{")
        latex_config.append(f"{current_indent}  \\newfontfamily\\emojifont{{{fallback_font}}}[Renderer=HarfBuzz]")
        latex_config.append(f"{current_indent}  \\typeout{{Using {fallback_font} for emoji rendering}}")
        latex_config.append(f"{current_indent}}}{{")
        current_indent += "  "
    latex_config.append(f"{current_indent}\\let\\emojifont\\rmfamily")
    latex_config.append(f"{current_indent}\\typeout{{Warning: No suitable emoji font found, using main font}}")
    for _ in range(len(fallback_fonts) + 1):
        current_indent = current_indent[:-2]
        latex_config.append(f"{current_indent}}}")
    return "\n".join(latex_config)

def configure_emoji_fonts_for_template(template_vars):
    emoji_fonts_info = detect_emoji_fonts()
    font_config = generate_emoji_font_config(emoji_fonts_info)
    template_vars['emoji_font_config'] = font_config
    template_vars['primary_emoji_font'] = emoji_fonts_info['primary']
    template_vars['emoji_fonts_available'] = emoji_fonts_info['available']
    template_vars['emoji_fallback_fonts'] = emoji_fonts_info['fallbacks']
    return template_vars

def validate_emoji_support_requirements(emoji: bool, diagnostics_mode: bool = False) -> dict:
    # 简化版省略详细诊断逻辑，仅调用 detect_emoji_fonts 并返回结构
    validation_result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'engine': 'lualatex' if emoji else 'xelatex',
        'emoji_fonts': detect_emoji_fonts(),
        'diagnostics': [],
        'system_info': {}
    }
    return validation_result

def _analyze_pandoc_error(error, emoji, pdf_engine, emoji_validation):
    """分析 Pandoc 错误并提供重试建议"""
    error_analysis = {
        'retry_recommended': False,
        'retry_reason': '',
        'suggested_fixes': []
    }
    
    error_message = str(error.stderr) if hasattr(error, 'stderr') else str(error)
    
    # 常见错误模式分析
    if 'xelatex' in error_message.lower() and 'not found' in error_message.lower():
        error_analysis['retry_recommended'] = True
        error_analysis['retry_reason'] = 'XeLaTeX engine issue detected, trying basic fallback'
        error_analysis['suggested_fixes'] = ['remove_shell_escape']
    elif 'timeout' in error_message.lower():
        error_analysis['retry_recommended'] = True  
        error_analysis['retry_reason'] = 'Timeout detected, retrying with extended timeout'
    elif emoji and 'lua' in error_message.lower():
        error_analysis['retry_recommended'] = True
        error_analysis['retry_reason'] = 'Emoji/Lua filter issue, trying without emoji filters'
        error_analysis['suggested_fixes'] = ['remove_emoji_filters']
    
    return error_analysis

def _apply_error_fixes(cmd, suggested_fixes):
    """根据错误分析应用修复建议"""
    new_cmd = cmd.copy()
    
    for fix in suggested_fixes:
        if fix == 'remove_shell_escape':
            # 移除 shell-escape 选项
            new_cmd = [arg for arg in new_cmd if '--pdf-engine-opt=-shell-escape' not in arg]
        elif fix == 'remove_emoji_filters':
            # 移除emoji相关的lua过滤器
            new_cmd = [arg for arg in new_cmd if 'emoji' not in arg.lower()]
    
    return new_cmd

def _handle_final_pandoc_failure(error, emoji, pdf_engine, emoji_validation, tmp_path, template_path, emoji_filter_path):
    """处理最终的 Pandoc 失败"""
    print("❌ PDF generation failed after all retry attempts")
    print("\n🔍 Error Analysis:")
    
    if hasattr(error, 'stderr') and error.stderr:
        print(f"   Pandoc stderr: {error.stderr[:500]}...")
    
    print(f"   PDF Engine: {pdf_engine}")
    print(f"   Emoji enabled: {emoji}")
    print(f"   Template: {template_path}")
    
    print("\n💡 Troubleshooting suggestions:")
    print("   1. Check if XeLaTeX/LuaLaTeX is properly installed")
    print("   2. Verify template.tex syntax")
    print("   3. Try without emoji support (remove --emoji flag)")
    print("   4. Check intermediate markdown file for issues")
    print(f"   5. Debug file: {tmp_path}")
    
    print("\n📋 For detailed diagnostics, run:")
    print("   python cli.py --diagnostics <book_dir>")
