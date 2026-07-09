#!/usr/bin/env python3
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
import yt_dlp

def parse_arguments():
    parser = argparse.ArgumentParser(description='Download YouTube content')
    parser.add_argument('--url', required=True, help='YouTube URL')
    parser.add_argument('--type', required=True, choices=['video', 'playlist', 'channel'],
                       help='Type of content to download')
    parser.add_argument('--quality', default='best',
                       choices=['best', '1080p', '720p', '480p', '360p', 'audio_only'],
                       help='Video quality')
    parser.add_argument('--output-format', default='mp4',
                       choices=['mp4', 'webm', 'mkv'],
                       help='Output format')
    parser.add_argument('--max-duration', type=int, default=0,
                       help='Maximum duration in minutes')
    parser.add_argument('--max-count', type=int, default=0,
                       help='Maximum number of videos to download')
    return parser.parse_args()

def get_quality_format(quality, output_format):
    """Get yt-dlp format string based on quality selection"""
    format_map = {
        'best': f'bestvideo[ext={output_format}]+bestaudio[ext=m4a]/best[ext={output_format}]/best',
        '1080p': f'bestvideo[height<=1080][ext={output_format}]+bestaudio[ext=m4a]/best[height<=1080][ext={output_format}]',
        '720p': f'bestvideo[height<=720][ext={output_format}]+bestaudio[ext=m4a]/best[height<=720][ext={output_format}]',
        '480p': f'bestvideo[height<=480][ext={output_format}]+bestaudio[ext=m4a]/best[height<=480][ext={output_format}]',
        '360p': f'bestvideo[height<=360][ext={output_format}]+bestaudio[ext=m4a]/best[height<=360][ext={output_format}]',
        'audio_only': 'bestaudio/best'
    }
    return format_map.get(quality, 'best')

def get_output_template(download_type, url):
    """Generate output template based on download type"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if download_type == 'video':
        return f'downloads/%(title)s.%(ext)s'
    elif download_type == 'playlist':
        return f'downloads/playlists/%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'
    elif download_type == 'channel':
        return f'downloads/channels/%(uploader)s/%(title)s.%(ext)s'
    else:
        return f'downloads/%(title)s.%(ext)s'

def download_content(url, download_type, quality, output_format, max_duration, max_count):
    """Download YouTube content with specified parameters"""
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': get_quality_format(quality, output_format),
        'outtmpl': get_output_template(download_type, url),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'nooverwrites': True,
        'continuedl': True,
        'writethumbnail': True,
        'writeinfojson': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US'],
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': output_format,
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            },
            {
                'key': 'FFmpegMetadata',
            }
        ],
        'logger': MyLogger(),
        'progress_hooks': [progress_hook],
    }
    
    # Add duration filter if specified
    if max_duration > 0:
        ydl_opts['match_filter'] = lambda info: (
            None if info.get('duration', 0) <= max_duration * 60 
            else f'Video duration {info.get("duration", 0)/60:.1f} minutes exceeds limit'
        )
    
    # Add count limit for playlists
    if download_type in ['playlist', 'channel'] and max_count > 0:
        ydl_opts['playlistend'] = max_count
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🎬 Downloading: {url}")
            print(f"📁 Type: {download_type}")
            print(f"🎯 Quality: {quality}")
            print(f"📦 Format: {output_format}")
            print("-" * 50)
            
            ydl.download([url])
            
    except Exception as e:
        print(f"❌ Error downloading: {str(e)}")
        sys.exit(1)

class MyLogger:
    def debug(self, msg):
        # Skip debug messages for cleaner output
        pass
    
    def warning(self, msg):
        print(f"⚠️  {msg}")
    
    def error(self, msg):
        print(f"❌ {msg}")

def progress_hook(d):
    if d['status'] == 'downloading':
        if 'total_bytes' in d:
            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            print(f"⬇️  Downloading: {percent:.1f}%", end='\r')
    elif d['status'] == 'finished':
        print(f"\n✅ Downloaded: {d['filename']}")

def main():
    args = parse_arguments()
    
    # Create necessary directories
    Path('downloads').mkdir(exist_ok=True)
    Path('downloads/playlists').mkdir(exist_ok=True)
    Path('downloads/channels').mkdir(exist_ok=True)
    
    # Download content
    download_content(
        args.url,
        args.type,
        args.quality,
        args.output_format,
        args.max_duration,
        args.max_count
    )
    
    print("\n" + "="*50)
    print("✅ Download completed successfully!")
    print("📁 Files saved in 'downloads/' directory")
    print("="*50)

if __name__ == '__main__':
    main()
