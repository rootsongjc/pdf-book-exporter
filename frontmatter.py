import yaml

def parse_front_matter(path):
    title = None
    weight = 9999
    draft = False
    publish = True
    export_pdf = True
    inside = False
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == '---':
                if not inside:
                    inside = True
                    continue
                else:
                    break
            if inside:
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('weight:'):
                    try:
                        weight = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('draft:'):
                    draft_value = line.split(':', 1)[1].strip().lower()
                    draft = draft_value in ['true', '1', 'yes']
                elif line.startswith('publish:'):
                    publish_value = line.split(':', 1)[1].strip().lower()
                    publish = publish_value in ['true', '1', 'yes']
                elif line.startswith('export_pdf:'):
                    export_pdf_value = line.split(':', 1)[1].strip().lower()
                    export_pdf = export_pdf_value in ['true', '1', 'yes']
                elif line.startswith('pdf:'):
                    pdf_value = line.split(':', 1)[1].strip().lower()
                    export_pdf = pdf_value in ['true', '1', 'yes']
    return title, weight, draft, publish, export_pdf

def should_include(path: str, metadata: tuple = None, include_drafts: bool = False) -> bool:
    if metadata is None:
        import frontmatter
        _, _, draft, publish, export_pdf = parse_front_matter(path)
    else:
        _, _, draft, publish, export_pdf = metadata
    if draft and not include_drafts:
        return False
    if not publish:
        return False
    if not export_pdf:
        return False
    return True

def load_book_config(book_dir):
    """Load book configuration from the _index.md front matter."""
    import os
    from tree import find_asset
    
    index_path = None
    for name in ("_index.md", "index.md"):
        candidate = os.path.join(book_dir, name)
        if os.path.exists(candidate):
            index_path = candidate
            break
    
    if not index_path:
        return {}
    
    config = {}
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract front matter
    if content.startswith('---'):
        try:
            # Find the end of front matter
            end_pos = content.find('\n---\n', 3)
            if end_pos != -1:
                front_matter = content[3:end_pos]
                metadata = yaml.safe_load(front_matter)
                
                # Extract book configuration if it exists
                if isinstance(metadata, dict) and 'book' in metadata:
                    book_config = metadata['book']
                    # Map book config to expected format
                    config = {
                        'title': book_config.get('title', metadata.get('title', 'Book')),
                        'author': book_config.get('author', 'Author'),
                        'date': str(book_config.get('date', metadata.get('date', '2024'))).split('T')[0],
                        'description': book_config.get('description', metadata.get('description', '')),
                        'language': book_config.get('language', 'zh-hans'),
                        'cover': book_config.get('cover', None),
                        'website': book_config.get('website', ''),
                        'appendix': book_config.get('appendix', False),
                        'subject': book_config.get('subject', book_config.get('description', metadata.get('description', ''))),
                        'keywords': book_config.get('keywords', ''),
                        'creator': book_config.get('creator', 'LaTeX with hyperref'),
                        'producer': book_config.get('producer', 'XeLaTeX'),
                        
                        # Enhanced cover configuration
                        'cover_config': {
                            'image': book_config.get('cover', None),
                            'title_text': book_config.get('cover_title_text', book_config.get('title', metadata.get('title', 'Book'))),
                            'author_text': book_config.get('cover_author_text', book_config.get('author', 'Author')),
                            'subtitle_text': book_config.get('cover_subtitle_text', ''),
                            'title_color': book_config.get('cover_title_color', '#000000'),
                            'author_color': book_config.get('cover_author_color', '#333333'),
                            'subtitle_color': book_config.get('cover_subtitle_color', '#666666'),
                            'title_font_size': book_config.get('cover_title_font_size', 48),
                            'author_font_size': book_config.get('cover_author_font_size', 24),
                            'subtitle_font_size': book_config.get('cover_subtitle_font_size', 18),
                            'title_position': book_config.get('cover_title_position', 'center'),
                            'author_position': book_config.get('cover_author_position', 'bottom'),
                            'overlay_enabled': book_config.get('cover_overlay_enabled', True),
                            'text_shadow': book_config.get('cover_text_shadow', True),
                            'background_overlay': book_config.get('cover_background_overlay', False),
                            'overlay_opacity': book_config.get('cover_overlay_opacity', 0.7)
                        },
                        
                        # Back-cover configuration (enhanced with text, QR code, and link)
                        'backcover_image': book_config.get('backcover_image', None),
                        'backcover_text': book_config.get('backcover_text', None),
                        'qrcode_image': book_config.get('qrcode_image', None),
                        'backcover_link_text': book_config.get('backcover_link_text', None),
                        'backcover_link_url': book_config.get('backcover_link_url', None),
                        
                        # Back-cover styling options
                        'backcover_text_color': book_config.get('backcover_text_color', '#000000'),
                        'backcover_link_color': book_config.get('backcover_link_color', '#0066CC'),
                        'backcover_text_font_size': book_config.get('backcover_text_font_size', 16),
                        'backcover_link_font_size': book_config.get('backcover_link_font_size', 14),
                        'qrcode_size': book_config.get('qrcode_size', '0.15\\paperwidth'),
                        'backcover_top_margin': book_config.get('backcover_top_margin', '0.2\\textheight'),
                        'backcover_bottom_margin': book_config.get('backcover_bottom_margin', '0.2\\textheight'),
                        'backcover_spacing_1': book_config.get('backcover_spacing_1', '1.5cm'),
                        'backcover_spacing_2': book_config.get('backcover_spacing_2', '1cm'),
                        
                        # Typography and styling configuration
                        'typography': {
                            'body_color': book_config.get('body_color', '#000000'),
                            'heading_color': book_config.get('heading_color', '#000000'),
                            'link_color': book_config.get('link_color', '#0066cc'),
                            'code_color': book_config.get('code_color', '#d14'),
                            'quote_color': book_config.get('quote_color', '#666666'),
                            'caption_color': book_config.get('caption_color', '#666666')
                        }
                    }
                else:
                    # Fallback to using main front matter
                    config = {
                        'title': metadata.get('title', 'Book'),
                        'author': metadata.get('author', 'Author'),
                        'date': str(metadata.get('date', '2024')).split('T')[0] if metadata.get('date') else '2024',
                        'description': metadata.get('description', ''),
                        'language': 'zh-hans',
                        'cover_config': {
                            'overlay_enabled': True,
                            'title_color': '#000000',
                            'author_color': '#333333'
                        },
                        'typography': {
                            'body_color': '#000000',
                            'heading_color': '#000000'
                        }
                    }
        except Exception as e:
            print(f"Warning: Failed to parse front matter: {e}")
            config = {
                'title': 'Book', 
                'author': 'Author', 
                'date': '2024', 
                'language': 'zh-hans',
                'cover_config': {'overlay_enabled': True},
                'typography': {'body_color': '#000000'}
            }
    
    # Print config for debugging
    print(f"Loaded book configuration with backcover: {config.get('backcover_image', 'None')}")
    return config
