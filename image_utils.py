import os
import re
import shutil
import hashlib
import subprocess
from pathlib import Path
import cache_utils

def latex_escape(s):
    return s.replace('\\', '/').replace('_', '\\_').replace('#', '\\#').replace('%', '\\%').replace('&', '\\&').replace(' ', '\\ ')

def download_image(url, output_path):
    import urllib.request
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        print(f"Downloaded {url} to {output_path}")
        return True
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return False

def find_image_file_recursive(book_dir, img_name, current_file_path):
    img_name = img_name.split('?')[0].split('#')[0]
    current_dir = os.path.dirname(current_file_path)
    candidate = os.path.abspath(os.path.join(current_dir, img_name))
    if os.path.exists(candidate):
        return candidate
    candidates = [
        os.path.join(book_dir, img_name),
        os.path.join(book_dir, 'images', img_name),
        os.path.join('static', 'images', img_name),
        os.path.join('static', 'files', img_name),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for root, dirs, files in os.walk(book_dir):
        if img_name in files:
            return os.path.join(root, img_name)
    for static_dir in ['static/images', 'static/files']:
        for root, dirs, files in os.walk(static_dir):
            if img_name in files:
                return os.path.join(root, img_name)
    return None

def convert_svg_to_png(svg_path, output_dir, cache_dir=None):
    if cache_dir:
        import cache_utils
        cached_path = cache_utils.get_cached_image(svg_path, cache_dir, '.png')
        if cached_path:
            output_name = os.path.splitext(os.path.basename(svg_path))[0] + '.png'
            output_path = os.path.join(output_dir, output_name)
            shutil.copy2(cached_path, output_path)
            return output_path
    svg2png_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/svg2png.sh'))
    if not os.path.exists(svg2png_script):
        print(f"svg2png.sh not found at {svg2png_script}")
        return None
    svg_name = os.path.basename(svg_path)
    png_name = svg_name.replace('.svg', '.png')
    png_path = os.path.join(output_dir, png_name)
    try:
        subprocess.run([svg2png_script, svg_path, png_path], check=True)
        if os.path.exists(png_path):
            print(f"Converted {svg_path} to {png_path} (via svg2png.sh)")
            if cache_dir:
                cache_utils.save_to_cache(svg_path, png_path, cache_dir)
            return png_path
        else:
            print(f"svg2png.sh did not produce {png_path}")
            return None
    except Exception as e:
        print(f"Error using svg2png.sh: {e}")
        return None

def convert_webp_to_png(webp_path, output_dir, cache_dir=None):
    if cache_dir:
        import cache_utils
        cached_path = cache_utils.get_cached_image(webp_path, cache_dir, '.png')
        if cached_path:
            output_name = os.path.splitext(os.path.basename(webp_path))[0] + '.png'
            output_path = os.path.join(output_dir, output_name)
            shutil.copy2(cached_path, output_path)
            return output_path
    try:
        webp_name = os.path.basename(webp_path)
        png_name = webp_name.replace('.webp', '.png')
        png_path = os.path.join(output_dir, png_name)
        cmd = ['magick', webp_path, png_path]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Converted {webp_path} to {png_path}")
        if cache_dir:
            cache_utils.save_to_cache(webp_path, png_path, cache_dir)
        return png_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Warning: Could not convert {webp_path} to PNG. Install ImageMagick.")
        return None

def process_images_in_content(content, book_dir, temp_dir, temp_pngs, current_file_path, cache_dir=None):
    os.makedirs(temp_dir, exist_ok=True)
    processed_images = {}
    content = re.sub(r'```mermaid[\s\S]*?```', '', content)
    def replace_image(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        if img_path.startswith('http://') or img_path.startswith('https://'):
            url_hash = hashlib.md5(img_path.encode()).hexdigest()[:12]
            original_filename = os.path.basename(img_path.split('?')[0])
            base_name = os.path.splitext(original_filename)[0]
            ext = os.path.splitext(original_filename)[1].lower()
            cached_filename = f"{base_name}_{url_hash}.png"
            cached_path = os.path.join(cache_dir, cached_filename) if cache_dir else None
            metadata = {}
            if cache_dir:
                import cache_utils
                metadata = cache_utils.load_cache_metadata(cache_dir)
            if cache_dir and cached_filename in metadata and os.path.exists(cached_path):
                print(f"Using cached remote image: {cached_path}")
                abs_path = cached_path
            else:
                temp_download_path = os.path.join(temp_dir, f"download_{url_hash}{ext}")
                if download_image(img_path, temp_download_path):
                    if ext == '.webp':
                        png_path = convert_webp_to_png(temp_download_path, temp_dir, cache_dir)
                        if png_path:
                            shutil.copy2(png_path, cached_path)
                            if cache_dir:
                                metadata[cached_filename] = {
                                    'source_url': img_path,
                                    'cached_at': __import__('time').time(),
                                    'cache_path': cached_path
                                }
                                cache_utils.save_cache_metadata(cache_dir, metadata)
                            abs_path = cached_path
                        else:
                            print(f"Warning: Failed to convert downloaded WebP to PNG: {img_path}")
                            return match.group(0)
                    elif ext == '.svg':
                        png_path = convert_svg_to_png(temp_download_path, temp_dir, cache_dir)
                        if png_path:
                            shutil.copy2(png_path, cached_path)
                            if cache_dir:
                                metadata[cached_filename] = {
                                    'source_url': img_path,
                                    'cached_at': __import__('time').time(),
                                    'cache_path': cached_path
                                }
                                cache_utils.save_cache_metadata(cache_dir, metadata)
                            abs_path = cached_path
                        else:
                            print(f"Warning: Failed to convert downloaded SVG to PNG: {img_path}")
                            return match.group(0)
                    else:
                        try:
                            if ext == '.gif':
                                cmd = ['magick', temp_download_path + '[0]', cached_path]
                            else:
                                cmd = ['magick', temp_download_path, cached_path]
                            subprocess.run(cmd, check=True, capture_output=True)
                            if cache_dir:
                                metadata[cached_filename] = {
                                    'source_url': img_path,
                                    'cached_at': __import__('time').time(),
                                    'cache_path': cached_path
                                }
                                cache_utils.save_cache_metadata(cache_dir, metadata)
                            abs_path = cached_path
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            print(f"Warning: Could not convert downloaded image {img_path} to PNG")
                            shutil.copy2(temp_download_path, cached_path)
                            if cache_dir:
                                metadata[cached_filename] = {
                                    'source_url': img_path,
                                    'cached_at': __import__('time').time(),
                                    'cache_path': cached_path
                                }
                                cache_utils.save_cache_metadata(cache_dir, metadata)
                            abs_path = cached_path
                    if os.path.exists(temp_download_path):
                        os.remove(temp_download_path)
                else:
                    print(f"Warning: Failed to download image: {img_path}")
                    return f"\n<!-- Image not available: {img_path} -->\n"
        else:
            abs_path = find_image_file_recursive(book_dir, img_path, current_file_path)
            if not abs_path:
                print(f"Warning: Image not found: {img_path} in {current_file_path}")
                return match.group(0)
        if abs_path in processed_images:
            escaped_path = processed_images[abs_path]
            latex = ('\n\\begin{figure}[htbp]\n' +
                '  \\centering\n' +
                f'  \\includegraphics[width=0.8\\textwidth]{{{escaped_path}}}\n' +
                f'  \\caption{{{alt_text}}}\n' +
                '\\end{figure}\n')
            return latex
        ext = os.path.splitext(abs_path)[1].lower()
        target_path = ''
        if ext == '.svg':
            png_path = convert_svg_to_png(abs_path, temp_dir, cache_dir)
            if not png_path or not os.path.exists(png_path):
                print(f"Warning: Failed to convert SVG to PNG: {abs_path}")
                return match.group(0)
            base_name = os.path.splitext(os.path.basename(abs_path))[0]
            unique_name = f"{base_name}.png"
            target_path = os.path.join(temp_dir, unique_name)
            if png_path != target_path:
                shutil.copy(png_path, target_path)
            temp_pngs.append(target_path)
        elif ext == '.webp':
            png_path = convert_webp_to_png(abs_path, temp_dir, cache_dir)
            if not png_path or not os.path.exists(png_path):
                print(f"Warning: Failed to convert WEBP to PNG: {abs_path}")
                return match.group(0)
            base_name = os.path.splitext(os.path.basename(abs_path))[0]
            unique_name = f"{base_name}.png"
            target_path = os.path.join(temp_dir, unique_name)
            if png_path != target_path:
                shutil.copy(png_path, target_path)
            temp_pngs.append(target_path)
        else:
            unique_name = os.path.basename(abs_path)
            target_path = os.path.join(temp_dir, unique_name)
            shutil.copy(abs_path, target_path)
            temp_pngs.append(target_path)
        escaped_path = latex_escape(target_path)
        processed_images[abs_path] = escaped_path
        latex = ('\n\\begin{figure}[htbp]\n' +
            '  \\centering\n' +
            f'  \\includegraphics[width=0.8\\textwidth]{{{escaped_path}}}\n' +
            f'  \\caption{{{alt_text}}}\n' +
            '\\end{figure}\n')
        return latex
    content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, content)
    content = re.sub(r'\n\s*({[^{]*}|\{:[^}]*\}|<!--.*?-->)', '\n', content)
    content = re.sub(r'{{[%<][\s\S]*?[%>]}}', '', content)
    return content

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
                    cached_cover = _get_cached_image_by_key(cache_key, cache_dir, '.png')
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
                        _save_to_cache_with_key(cache_key, png_cover_path, cache_dir)
                    
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


def _get_cached_image_by_key(cache_key, cache_dir, extension='.png'):
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


def _save_to_cache_with_key(cache_key, file_path, cache_dir):
    """Save file to cache with a specific cache key."""
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


def get_available_fonts():
    """Get available fonts for Chinese text on the system."""
    import subprocess
    
    try:
        # Check for available Chinese fonts
        result = subprocess.run(['fc-list', ':', 'family'], 
                              capture_output=True, text=True, check=True)
        fonts = result.stdout.split('\n')
        
        # Priority list of preferred Chinese fonts
        preferred_fonts = [
            'Source Han Sans SC',      # Adobe/Google 思源黑体
            'Noto Sans CJK SC',       # Google Noto Sans CJK
            'PingFang SC',            # macOS 默认中文字体
            'STSong',                 # macOS 宋体
            'FangSong',               # 仿宋
            'Hiragino Mincho Pro',    # 日文字体
            'Times New Roman',        # Fallback serif font
            'DejaVu Serif'            # Universal fallback
        ]
        
        # Find the first available font
        for font in preferred_fonts:
            if any(font in line for line in fonts):
                return font
        return 'Source Han Sans SC'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'Source Han Sans SC'
