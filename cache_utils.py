import os
import json
import shutil
import hashlib
import time
from pathlib import Path

def get_file_hash(file_path):
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def get_cache_dir(book_dir):
    book_dir = os.path.abspath(book_dir)
    current_dir = book_dir
    book_root_dir = book_dir
    while current_dir and current_dir != os.path.dirname(current_dir):
        parent = os.path.dirname(current_dir)
        parent_name = os.path.basename(parent)
        if parent_name == "book":
            book_root_dir = current_dir
            break
        current_dir = parent
    cache_dir = os.path.join(book_root_dir, 'image-caches')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_cache_metadata_path(cache_dir):
    return os.path.join(cache_dir, 'cache_metadata.json')

def load_cache_metadata(cache_dir):
    metadata_path = get_cache_metadata_path(cache_dir)
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache metadata: {e}")
    return {}

def save_cache_metadata(cache_dir, metadata):
    metadata_path = get_cache_metadata_path(cache_dir)
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache metadata: {e}")

def get_cached_image(source_path, cache_dir, target_extension='.png'):
    if not os.path.exists(source_path):
        return None
    source_hash = get_file_hash(source_path)
    if not source_hash:
        return None
    source_name = os.path.basename(source_path)
    base_name = os.path.splitext(source_name)[0]
    cache_filename = f"{base_name}_{source_hash[:12]}{target_extension}"
    cache_path = os.path.join(cache_dir, cache_filename)
    metadata = load_cache_metadata(cache_dir)
    if os.path.exists(cache_path):
        cache_info = metadata.get(cache_filename, {})
        cached_hash = cache_info.get('source_hash')
        if cached_hash == source_hash:
            print(f"Using cached image: {cache_path}")
            return cache_path
        else:
            print(f"Cache invalid for {source_path}, removing old cache")
            try:
                os.remove(cache_path)
                if cache_filename in metadata:
                    del metadata[cache_filename]
                    save_cache_metadata(cache_dir, metadata)
            except Exception as e:
                print(f"Error removing old cache: {e}")
    return None

def save_to_cache(source_path, converted_path, cache_dir):
    if not os.path.exists(source_path) or not os.path.exists(converted_path):
        return None
    source_hash = get_file_hash(source_path)
    if not source_hash:
        return None
    source_name = os.path.basename(source_path)
    base_name = os.path.splitext(source_name)[0]
    target_extension = os.path.splitext(converted_path)[1]
    cache_filename = f"{base_name}_{source_hash[:12]}{target_extension}"
    cache_path = os.path.join(cache_dir, cache_filename)
    try:
        shutil.copy2(converted_path, cache_path)
        metadata = load_cache_metadata(cache_dir)
        metadata[cache_filename] = {
            'source_path': os.path.abspath(source_path),
            'source_hash': source_hash,
            'cached_at': time.time(),
            'cache_path': cache_path
        }
        save_cache_metadata(cache_dir, metadata)
        print(f"Saved to cache: {cache_path}")
        return cache_path
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return None

def get_cached_image_by_key(cache_key, cache_dir, extension='.png'):
    try:
        metadata = load_cache_metadata(cache_dir)
        for filename, info in metadata.items():
            if info.get('cache_key') == cache_key:
                cache_path = info.get('cache_path')
                if cache_path and os.path.exists(cache_path):
                    return cache_path
    except Exception as e:
        print(f"Error checking cache: {e}")
    return None

def save_to_cache_with_key(cache_key, file_path, cache_dir):
    try:
        cache_filename = f"{cache_key}.png"
        cache_path = os.path.join(cache_dir, cache_filename)
        shutil.copy2(file_path, cache_path)
        metadata = load_cache_metadata(cache_dir)
        metadata[cache_filename] = {
            'cache_key': cache_key,
            'cached_at': time.time(),
            'cache_path': cache_path
        }
        save_cache_metadata(cache_dir, metadata)
        print(f"Cached enhanced image: {cache_path}")
        return cache_path
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return None

def clean_cache(book_dir, days_old=30):
    cache_dir = get_cache_dir(book_dir)
    if not os.path.exists(cache_dir):
        print("No cache directory found.")
        return
    metadata = load_cache_metadata(cache_dir)
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)
    cleaned_count = 0
    for cache_filename, cache_info in list(metadata.items()):
        cached_at = cache_info.get('cached_at', 0)
        cache_path = cache_info.get('cache_path', os.path.join(cache_dir, cache_filename))
        if cached_at < cutoff_time or not os.path.exists(cache_path):
            try:
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                del metadata[cache_filename]
                cleaned_count += 1
                print(f"Removed cache: {cache_filename}")
            except Exception as e:
                print(f"Error removing cache {cache_filename}: {e}")
    if cleaned_count > 0:
        save_cache_metadata(cache_dir, metadata)
        print(f"Cleaned {cleaned_count} cache files older than {days_old} days.")
    else:
        print("No cache files to clean.")

def show_cache_info(book_dir):
    cache_dir = get_cache_dir(book_dir)
    if not os.path.exists(cache_dir):
        print("No cache directory found.")
        return
    metadata = load_cache_metadata(cache_dir)
    print(f"Cache directory: {cache_dir}")
    print(f"Cache files: {len(metadata)}")
    if metadata:
        total_size = 0
        for cache_filename, cache_info in metadata.items():
            cache_path = cache_info.get('cache_path', os.path.join(cache_dir, cache_filename))
            if os.path.exists(cache_path):
                size = os.path.getsize(cache_path)
                total_size += size
                cached_at = cache_info.get('cached_at', 0)
                age_days = (time.time() - cached_at) / (24 * 60 * 60)
                print(f"  {cache_filename}: {size/1024:.1f}KB, {age_days:.1f} days old")
        print(f"Total cache size: {total_size/1024/1024:.2f}MB")
