import os
from datetime import datetime
import tempfile
import tree
import emoji_support
import cache_utils

def build_pdf_xelatex(book_dir, root_node, output_pdf, metadata, template_path_arg=None, appendix_path=None, emoji=False, max_table_width=0.98):
    import os
    import subprocess
    from datetime import datetime
    import shutil
    import re
    import time
    import uuid
    # 统一前缀
    import cache_utils
    import tree
    import emoji_support
    import image_utils
    
    success = False

    available_font = image_utils.get_available_fonts() if hasattr(image_utils, 'get_available_fonts') else metadata.get('font')
    cache_dir = cache_utils.get_cache_dir(book_dir)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pngs = []
        emoji_commands_content = ""
        if emoji:
            script_dir = os.path.dirname(__file__)
            emoji_commands_src = os.path.join(script_dir, 'emoji-commands.tex')
            if os.path.exists(emoji_commands_src):
                with open(emoji_commands_src, 'r', encoding='utf-8') as f:
                    emoji_commands_content = f.read()
                pass  # Emoji commands loaded successfully
            else:
                pass  # Emoji commands file not found, will use defaults

        cover_config = metadata.get('cover_config', {})
        cover_file = cover_config.get('image') or metadata.get('cover')
        if cover_file:
            cover_path = tree.find_asset(book_dir, [cover_file])
        else:
            cover_path = tree.find_asset(book_dir, ['cover.webp', 'cover.jpg', 'cover.png'])

        backcover_path = None
        backcover_image = metadata.get('backcover_image')
        if backcover_image:
            if os.path.isabs(backcover_image) and os.path.exists(backcover_image):
                backcover_path = backcover_image
                pass  # Using configured backcover image
            else:
                backcover_path = tree.find_asset(book_dir, [backcover_image])
                if not backcover_path:
                    pass  # Backcover image not found, will continue without
        else:
            backcover_path = tree.find_asset(book_dir, ['backcover.webp', 'backcover.jpg', 'backcover.png'])
            if backcover_path:
                pass  # Using default backcover image

        processed_cover_path = None
        processed_backcover_path = None
        if cover_path:
            if cover_path.lower().endswith('.webp'):
                # Converting WebP cover to PNG for LaTeX compatibility
                converted_cover = image_utils.convert_webp_to_png(cover_path, temp_dir, cache_dir)
                if converted_cover:
                    prepared_cover = image_utils.prepare_cover_for_latex(converted_cover, metadata, temp_dir, cache_dir)
                    processed_cover_path = prepared_cover or converted_cover
                    temp_pngs.append(converted_cover)
                    if prepared_cover and prepared_cover != converted_cover:
                        temp_pngs.append(prepared_cover)
                else:
                    pass  # Failed to convert WebP cover, continuing without
            else:
                prepared_cover = image_utils.prepare_cover_for_latex(cover_path, metadata, temp_dir, cache_dir)
                processed_cover_path = prepared_cover or cover_path
                if prepared_cover and prepared_cover != cover_path:
                    temp_pngs.append(prepared_cover)

        if backcover_path:
            if backcover_path.lower().endswith('.webp'):
                # Converting WebP backcover to PNG for LaTeX compatibility
                converted_backcover = image_utils.convert_webp_to_png(backcover_path, temp_dir, cache_dir)
                if converted_backcover:
                    processed_backcover_path = converted_backcover
                    temp_pngs.append(converted_backcover)
                else:
                    pass  # Failed to convert WebP backcover, continuing without
            else:
                processed_backcover_path = backcover_path

        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.md', prefix='debug_') as tmp:
            for child in root_node.children:
                tree.write_hierarchical_content(tmp, child, book_dir, temp_dir, temp_pngs, level=1, cache_dir=cache_dir, process_images_in_content=image_utils.process_images_in_content)
            tmp_path = tmp.name
            if appendix_path:
                with open(appendix_path, 'r', encoding='utf-8') as appendix_file:
                    tmp.write('\n\n')
                    tmp.write(appendix_file.read())

        emoji_validation = emoji_support.validate_emoji_support_requirements(emoji, diagnostics_mode=False)
        if not emoji_validation['valid']:
            print("\n❌ EMOJI SUPPORT VALIDATION FAILED")
            print("="*50)
            for error in emoji_validation['errors']:
                print(f"❌ {error}")
            print("\n💡 FALLBACK OPTIONS:")
            print("   1. Run without --emoji flag to use XeLaTeX")
            print("   2. Install missing dependencies and try again")
            print("   3. Run with --diagnostics for detailed troubleshooting")
            if emoji:
                print("\n🔄 ATTEMPTING GRACEFUL FALLBACK...")
                print("   Switching to XeLaTeX without emoji support...")
                try:
                    return build_pdf_xelatex(book_dir, root_node, output_pdf, metadata, template_path_arg, appendix_path, emoji=False, max_table_width=max_table_width)
                except Exception as fallback_error:
                    print(f"❌ Fallback also failed: {fallback_error}")
                    return False
            else:
                return False
        for warning in emoji_validation['warnings']:
            print(f"⚠️  {warning}")
        if 'system_info' in emoji_validation:
            system_info = emoji_validation['system_info']
            print(f"🖥️  System: {system_info.get('platform', 'Unknown')} (" f"{system_info.get('architecture', 'Unknown')})")
            if 'tex_distribution' in system_info:
                print(f"📄 LaTeX: {system_info['tex_distribution']}")

        if template_path_arg and os.path.exists(template_path_arg):
            template_path = template_path_arg
        else:
            template_path = os.path.join(os.path.dirname(__file__), 'template.tex')

        filters_dir = os.path.join(os.path.dirname(__file__), 'filters')
        cleanup_filter_path = os.path.join(filters_dir, 'cleanup-filter.lua')
        lua_filter_path = os.path.join(filters_dir, 'table-wrap.lua')
        minted_filter_path = os.path.join(filters_dir, 'minted-filter.lua')
        emoji_filter_path = os.path.join(filters_dir, 'emoji-passthrough.lua')
        symbol_filter_path = os.path.join(filters_dir, 'symbol-fallback-filter.lua')
        simple_image_attr_cleanup_path = os.path.join(filters_dir, 'simple-image-attr-cleanup.lua')

        pdf_engine = emoji_validation['engine']
        if emoji:
            print(f"✅ Emoji support enabled, using {pdf_engine.upper()} engine")

        cmd = [
            'pandoc',
            '-f', 'markdown+emoji',
            tmp_path,
            '-o',
            output_pdf,
            f'--pdf-engine={pdf_engine}',
            '--template=' + template_path,
            '-V', f'title={metadata.get("title", "Book")}',
            '-V', f'author={metadata.get("author", "Author")}',
            '-V', f'date={metadata.get("date", "2024")}',
            '--toc',
            '--toc-depth=4',
            '-V', 'geometry:margin=2.5cm',
            '-V', f'exported={datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '-V', f'website={metadata.get("website", "")}',
            '-V', f'subject={metadata.get("subject", "")}',
            '-V', f'keywords={metadata.get("keywords", "")}',
            '-V', f'creator={metadata.get("creator", "LaTeX with hyperref")}',
            '-V', f'producer={metadata.get("producer", "LuaLaTeX" if emoji else "XeLaTeX")}',
            '-V', 'fontsize=12pt',
            '-V', 'linestretch=1.5',
            '--listings',
            '--number-sections',
            '--top-level-division=chapter',
            f'--resource-path={temp_dir}',
            '-V', 'bookmarks=true',
            '-V', 'tables=true',
            '-V', f'max_table_width={max_table_width}',
            '--wrap=preserve'
        ]
        if pdf_engine == 'lualatex':
            cmd.extend([
                '--pdf-engine-opt=-shell-escape',
                '--pdf-engine-opt=--interaction=nonstopmode',
            ])
        else:
            cmd.extend([
                '--pdf-engine-opt=-shell-escape',
            ])
        if emoji:
            cmd.extend(['-V', 'emoji=true'])
            emoji_fonts_info = emoji_validation['emoji_fonts']
            if emoji_fonts_info and emoji_fonts_info.get('primary'):
                cmd.extend(['-V', f'primary_emoji_font={emoji_fonts_info["primary"]}'])
                print(f"🎨 Using emoji font: {emoji_fonts_info['primary']}")
            else:
                print("⚠️  No emoji font detected, using LaTeX emoji package defaults")
            try:
                if os.path.exists(emoji_filter_path):
                    cmd.extend([f'--lua-filter={emoji_filter_path}'])
                    print(f"✅ Added emoji filter: {emoji_filter_path}")
                else:
                    print(f"⚠️  Emoji filter not found at {emoji_filter_path}")
                    print("   Emoji processing will be limited to basic LaTeX font support")
            except Exception as e:
                print(f"⚠️  Error configuring emoji filter: {e}")
                print("   Continuing without emoji filter")
        cmd.extend(['--columns=120'])
        try:
            if os.path.exists(simple_image_attr_cleanup_path):
                cmd.extend([f'--lua-filter={simple_image_attr_cleanup_path}'])
                print(f"✅ Added simple image attribute cleanup filter: {simple_image_attr_cleanup_path}")
        except Exception as e:
            print(f"⚠️  Error adding simple image attribute cleanup filter: {e}")
        try:
            fix_lstinline_path = os.path.join(filters_dir, 'fix-lstinline.lua')
            if os.path.exists(fix_lstinline_path):
                cmd.extend([f'--lua-filter={fix_lstinline_path}'])
                print(f"✅ Added lstinline fix filter: {fix_lstinline_path}")
        except Exception as e:
            print(f"⚠️  Error adding lstinline fix filter: {e}")
        try:
            ansi_cleanup_path = os.path.join(filters_dir, 'ansi-cleanup.lua')
            if os.path.exists(ansi_cleanup_path):
                cmd.extend([f'--lua-filter={ansi_cleanup_path}'])
                print(f"✅ Added ANSI cleanup filter: {ansi_cleanup_path}")
        except Exception as e:
            print(f"⚠️  Error adding ANSI cleanup filter: {e}")
        try:
            if os.path.exists(cleanup_filter_path):
                cmd.extend([f'--lua-filter={cleanup_filter_path}'])
                print(f"✅ Added cleanup filter: {cleanup_filter_path}")
        except Exception as e:
            print(f"⚠️  Error adding cleanup filter: {e}")
        try:
            if os.path.exists(minted_filter_path):
                cmd.extend([f'--lua-filter={minted_filter_path}'])
                print(f"✅ Added minted filter: {minted_filter_path}")
        except Exception as e:
            print(f"⚠️  Error adding minted filter: {e}")
        try:
            if os.path.exists(symbol_filter_path):
                cmd.extend([f'--lua-filter={symbol_filter_path}'])
                print(f"✅ Added symbol fallback filter: {symbol_filter_path}")
        except Exception as e:
            print(f"⚠️  Error adding symbol fallback filter: {e}")
        try:
            if os.path.exists(lua_filter_path):
                cmd.extend([f'--lua-filter={lua_filter_path}'])
                print(f"✅ Added table-wrap filter: {lua_filter_path}")
        except Exception as e:
            print(f"⚠️  Error adding table-wrap filter: {e}")
        if processed_cover_path:
            cmd.extend(['-V', f'cover-image={os.path.abspath(processed_cover_path)}'])
        if processed_backcover_path:
            cmd.extend(['-V', f'backcover-image={os.path.abspath(processed_backcover_path)}'])
        qrcode_path = metadata.get('qrcode_image')
        if qrcode_path and os.path.exists(qrcode_path):
            cmd.extend(['-V', f'qrcode_image={os.path.abspath(qrcode_path)}'])
        else:
            default_qrcode_path = tree.find_asset(book_dir, ['qrcode.jpg', 'qrcode.png'])
            if default_qrcode_path:
                cmd.extend(['-V', f'qrcode_image={os.path.abspath(default_qrcode_path)}'])
        typography_config = metadata.get('typography', {})
        if typography_config:
            for color_key, color_value in typography_config.items():
                if color_value and color_value.startswith('#'):
                    clean_color = color_value.lstrip('#')
                    cmd.extend(['-V', f'{color_key}={clean_color}'])
        cover_config = metadata.get('cover_config', {})
        if cover_config and cover_config.get('overlay_enabled', True):
            if cover_config.get('title_text'):
                cmd.extend(['-V', f"cover_title_text={cover_config['title_text']}"])
            if cover_config.get('author_text'):
                cmd.extend(['-V', f"cover_author_text={cover_config['author_text']}"])
            if cover_config.get('subtitle_text'):
                cmd.extend(['-V', f"cover_subtitle_text={cover_config['subtitle_text']}"])
            export_date = datetime.now().strftime("%Y年%m月%d日")
            cmd.extend(['-V', f"cover_export_date={export_date}"])
            for color_key in ['title_color', 'author_color', 'subtitle_color']:
                color_value = cover_config.get(f'{color_key}')
                if color_value and color_value.startswith('#'):
                    clean_color = color_value.lstrip('#')
                    cmd.extend(['-V', f'cover_{color_key}={clean_color}'])
            title_pos = cover_config.get('title_position', 'center')
            author_pos = cover_config.get('author_position', 'bottom')
            cmd.extend(['-V', f'cover_title_position={title_pos}'])
            cmd.extend(['-V', f'cover_author_position={author_pos}'])
            title_size = cover_config.get('title_font_size', 48)
            author_size = cover_config.get('author_font_size', 24)
            subtitle_size = cover_config.get('subtitle_font_size', 18)
            title_line_height = int(title_size * 1.1)
            author_line_height = int(author_size * 1.33)
            subtitle_line_height = int(subtitle_size * 1.33)
            cmd.extend(['-V', f'cover_title_font_size={title_size}'])
            cmd.extend(['-V', f'cover_author_font_size={author_size}'])
            cmd.extend(['-V', f'cover_subtitle_font_size={subtitle_size}'])
            cmd.extend(['-V', f'cover_title_line_height={title_line_height}'])
            cmd.extend(['-V', f'cover_author_line_height={author_line_height}'])
            cmd.extend(['-V', f'cover_subtitle_line_height={subtitle_line_height}'])
        backcover_text = metadata.get('backcover_text')
        if backcover_text:
            import re
            backcover_text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', backcover_text)
            backcover_text = backcover_text.replace('\n', '\\newline ').replace('"', '\\"')
            cmd.extend(['-V', f'backcover_text={backcover_text}'])
        backcover_link_text = metadata.get('backcover_link_text')
        backcover_link_url = metadata.get('backcover_link_url')
        if backcover_link_text:
            cmd.extend(['-V', f'backcover_link_text={backcover_link_text}'])
        if backcover_link_url:
            cmd.extend(['-V', f'backcover_link_url={backcover_link_url}'])
        backcover_styling = {
            'backcover_text_color': metadata.get('backcover_text_color', '#000000'),
            'backcover_link_color': metadata.get('backcover_link_color', '#0066CC'),
            'backcover_text_font_size': metadata.get('backcover_text_font_size', 16),
            'backcover_link_font_size': metadata.get('backcover_link_font_size', 14),
            'backcover_text_line_height': int(metadata.get('backcover_text_font_size', 16) * 1.5),
            'backcover_link_line_height': int(metadata.get('backcover_link_font_size', 14) * 1.5),
            'qrcode_size': metadata.get('qrcode_size', '0.15\\paperwidth'),
            'backcover_top_margin': metadata.get('backcover_top_margin', '0.2\\textheight'),
            'backcover_bottom_margin': metadata.get('backcover_bottom_margin', '0.2\\textheight'),
            'backcover_spacing_1': metadata.get('backcover_spacing_1', '1.5cm'),
            'backcover_spacing_2': metadata.get('backcover_spacing_2', '1cm')
        }
        for key, value in backcover_styling.items():
            if isinstance(value, str) and value.startswith('#'):
                clean_color = value.lstrip('#')
                cmd.extend(['-V', f'{key}={clean_color}'])
            else:
                cmd.extend(['-V', f'{key}={value}'])
        start_time = time.time()
        print(f"🔧 Using PDF engine: {pdf_engine}")
        print(f"📐 Table width limit: {max_table_width * 100:.1f}% of text width")
        if emoji:
            print(f"🎨 Emoji support: enabled")
            if emoji_validation.get('emoji_fonts', {}).get('available'):
                primary_font = emoji_validation['emoji_fonts'].get('primary', 'Unknown')
                print(f"   Primary emoji font: {primary_font}")
        max_retries = 2
        retry_count = 0
        last_error = None
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    print(f"🔄 Retry attempt {retry_count}/{max_retries}...")
                print("🚀 Running Pandoc to generate PDF...")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
                break
            except subprocess.TimeoutExpired as e:
                last_error = e
                print(f"⏰ Pandoc execution timed out (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    print("   This might be due to complex content or system load...")
                    retry_count += 1
                    continue
                else:
                    print("❌ PDF generation failed due to timeout")
                    print("💡 Suggestions:")
                    print("   - Try with smaller content sections")
                    print("   - Check system resources")
                    print("   - Verify LaTeX installation is not corrupted")
                    return False
            except subprocess.CalledProcessError as e:
                last_error = e
                print(f'❌ Pandoc execution failed (attempt {retry_count + 1}): {e}')
                error_analysis = emoji_support._analyze_pandoc_error(e, emoji, pdf_engine, emoji_validation)
                if error_analysis['retry_recommended'] and retry_count < max_retries:
                    print(f"🔄 {error_analysis['retry_reason']}")
                    retry_count += 1
                    if error_analysis['suggested_fixes']:
                        print("   Applying suggested fixes...")
                        cmd = emoji_support._apply_error_fixes(cmd, error_analysis['suggested_fixes'])
                    continue
                else:
                    emoji_support._handle_final_pandoc_failure(e, emoji, pdf_engine, emoji_validation, tmp_path, template_path, emoji_filter_path)
                    return False
            except Exception as e:
                last_error = e
                print(f'❌ Unexpected error during PDF generation: {e}')
                if retry_count < max_retries:
                    print("🔄 Retrying with basic error recovery...")
                    retry_count += 1
                    continue
                else:
                    print(f"❌ All retry attempts failed. Last error: {e}")
                    print(f"📁 Debug files preserved:")
                    print(f"   Intermediate markdown: {tmp_path}")
                    return False
        try:
            if result.stderr:
                print(f"⚠️  Pandoc warnings:\n{result.stderr}")
            if not os.path.exists(output_pdf):
                print("❌ PDF file was not created despite successful Pandoc execution")
                return False
            print(f'✅ PDF generated successfully at {output_pdf}')
            success = True

            # Additionally export LaTeX source for debugging/diffing
            try:
                output_tex = os.path.splitext(output_pdf)[0] + '.tex'
                cmd_tex = [
                    'pandoc',
                    '-f', 'markdown+emoji',
                    tmp_path,
                    '-t', 'latex',
                    '-o', output_tex,
                    '--template=' + template_path,
                    '-V', f'title={metadata.get("title", "Book")}',
                    '-V', f'author={metadata.get("author", "Author")}',
                    '-V', f'date={metadata.get("date", "2024")}',
                    '--toc',
                    '--toc-depth=4',
                    '-V', 'geometry:margin=2.5cm',
                    '-V', f'exported={datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    '-V', f'website={metadata.get("website", "")}',
                    '-V', f'subject={metadata.get("subject", "")}',
                    '-V', f'keywords={metadata.get("keywords", "")}',
                    '-V', f'creator={metadata.get("creator", "LaTeX with hyperref")}',
                    '-V', f'producer={metadata.get("producer", "LuaLaTeX" if emoji else "XeLaTeX")}',
                    '-V', 'fontsize=12pt',
                    '-V', 'linestretch=1.5',
                    '--listings',
                    '--number-sections',
                    '--top-level-division=chapter',
                    f'--resource-path={temp_dir}',
                    '-V', 'bookmarks=true',
                    '-V', 'tables=true',
                    '-V', f'max_table_width={max_table_width}',
                    '--wrap=preserve',
                    '--columns=120'
                ]
                # Reuse the same filters (Lua filters are honored for LaTeX as well)
                for f in [emoji_filter_path, os.path.join(filters_dir, 'fix-lstinline.lua'), os.path.join(filters_dir, 'ansi-cleanup.lua'), os.path.join(filters_dir, 'minted-filter.lua'), cleanup_filter_path, symbol_filter_path, lua_filter_path]:
                    if os.path.exists(f):
                        cmd_tex.extend(['--lua-filter=' + f])
                tex_result = subprocess.run(cmd_tex, check=True, capture_output=True, text=True, timeout=300)
                if tex_result.stderr:
                    print(f"⚠️  LaTeX export warnings:\n{tex_result.stderr}")
                print(f"📝 LaTeX source exported: {output_tex}")
                
                # Clean up the generated .tex file after successful PDF generation
                try:
                    if os.path.exists(output_tex):
                        os.unlink(output_tex)
                        print(f"🗑️  Cleaned up LaTeX source file: {output_tex}")
                except Exception as cleanup_error:
                    print(f"⚠️  Failed to clean up LaTeX source file: {cleanup_error}")
                    
            except Exception as e:
                print(f"⚠️  Failed to export LaTeX source: {e}")

            end_time = time.time()
            processing_time = end_time - start_time
            try:
                pdf_size = os.path.getsize(output_pdf)
                page_count = "Unknown"
                try:
                    from PyPDF2 import PdfReader
                    pdf_reader = PdfReader(output_pdf)
                    page_count = len(pdf_reader.pages)
                except ImportError:
                    print("⚠️  PyPDF2 not available for page count")
                except Exception as e:
                    print(f"⚠️  Could not read PDF for page count: {e}")
                print("\n--- PDF Export Statistics ---")
                print(f"Engine: {pdf_engine.upper()}")
                print(f"File size: {pdf_size / 1024:.2f} KB")
                print(f"Page count: {page_count}")
                print(f"Processing time: {processing_time:.2f} seconds")
                if emoji:
                    print(f"Emoji support: ✅ Enabled")
                if page_count != "Unknown" and isinstance(page_count, int):
                    if page_count == 0:
                        print("⚠️  Warning: PDF appears to be empty")
                    elif page_count < 5:
                        print("⚠️  Warning: PDF has very few pages - check content processing")
            except Exception as e:
                print(f"⚠️  Error collecting PDF statistics: {e}")
                print(f"   PDF file exists at: {output_pdf}")
        finally:
            print(f"\n📁 Debug information:")
            print(f"   Intermediate markdown: {tmp_path}")
            print(f"   Template used: {template_path}")
            if emoji and os.path.exists(emoji_filter_path):
                print(f"   Emoji filter: {emoji_filter_path}")
            # os.unlink(tmp_path)
            # os.unlink(tmp_path)
        return success

def build_pdf(book_dir, root_node, output_pdf, metadata, template_path=None, appendix_path=None, emoji=False, max_table_width=0.98):
    return build_pdf_xelatex(book_dir, root_node, output_pdf, metadata, template_path, appendix_path, emoji, max_table_width)

def prepare_cover_for_latex(cover_path, config, temp_dir, cache_dir=None):
    """Prepare cover image for LaTeX processing without text overlay."""
    if not cover_path or not os.path.exists(cover_path):
        print("No cover image found")
        return None
        
    try:
        # Get cover configuration
        cover_config = config.get('cover_config', {})
        
        # If text overlay is disabled, just return the original image
        if not cover_config.get('overlay_enabled', True):
            print("Cover text overlay disabled, using original image")
            return cover_path
        
        # For WebP covers, convert to PNG for better LaTeX compatibility
        if cover_path.lower().endswith('.webp'):
            print(f"Converting WebP cover to PNG for LaTeX: {cover_path}")
            try:
                from PIL import Image
                import uuid
                
                # Generate cache key for WebP conversion
                source_hash = cache_utils.get_file_hash(cover_path)[:12] if cover_path else "default"
                cache_key = f"cover_png_{source_hash}"
                
                # Check cache first
                if cache_dir:
                    cached_cover = get_cached_image_by_key(cache_key, cache_dir, '.png')
                    if cached_cover:
                        print(f"Using cached PNG cover: {cached_cover}")
                        return cached_cover
                
                # Convert WebP to PNG
                with Image.open(cover_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    png_cover_path = os.path.join(temp_dir, f"cover_{uuid.uuid4().hex[:8]}.png")
                    img.save(png_cover_path, 'PNG', quality=95)
                    
                    # Cache the result
                    if cache_dir:
                        save_to_cache_with_key(cache_key, png_cover_path, cache_dir)
                    
                    print(f"Converted cover to PNG: {png_cover_path}")
                    return png_cover_path
                    
            except ImportError:
                print("PIL (Pillow) not available, using original WebP cover")
                return cover_path
            except Exception as e:
                print(f"Error converting WebP cover: {e}")
                return cover_path
        else:
            # For non-WebP images, use directly
            print(f"Using original cover image: {cover_path}")
            return cover_path
            
    except Exception as e:
        print(f"Error preparing cover: {e}")
        return cover_path


def get_cached_image_by_key(cache_key, cache_dir, extension='.png'):
    """Get cached image by cache key."""
    try:
        metadata = cache_utils.load_cache_metadata(cache_dir)
        for filename, info in metadata.items():
            if info.get('cache_key') == cache_key:
                cache_path = info.get('cache_path')
                if cache_path and os.path.exists(cache_path):
                    return cache_path
    except Exception as e:
        print(f"Error checking cache: {e}")
    return None


def save_to_cache_with_key(cache_key, file_path, cache_dir):
    """Save file to cache with a specific cache key."""
    import shutil
    import time
    
    try:
        cache_filename = f"{cache_key}.png"
        cache_path = os.path.join(cache_dir, cache_filename)
        
        # Copy file to cache
        shutil.copy2(file_path, cache_path)
        
        # Update metadata
        metadata = cache_utils.load_cache_metadata(cache_dir)
        metadata[cache_filename] = {
            'cache_key': cache_key,
            'cached_at': time.time(),
            'cache_path': cache_path
        }
        cache_utils.save_cache_metadata(cache_dir, metadata)
        
        print(f"Cached enhanced image: {cache_path}")
        return cache_path
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return None
