#!/usr/bin/env python3
"""
Online Media Downloader Module

Downloads videos from online platforms (YouTube, etc.) using yt-dlp.
Phase 1: YouTube support only (requires YouTube Premium for best results).
Phase 2+: Multi-platform support (Vimeo, Dailymotion, etc.).

Features:
- Auto-detects URLs vs local paths
- Smart caching (skip re-download)
- Format selection (best, 1080p, 720p, 480p, audio-only)
- Progress display
- Filename sanitization
- Error handling with retry logic

Related: PRD-2025-12-10-02-online-media-integration
         TRD-2025-12-10-02-online-media-integration
"""

# Standard library
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs

# Local
from shared.logger import get_logger

logger = get_logger(__name__)

# Lazy import yt-dlp (not always installed)
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    # Note: Warning will be shown by OnlineMediaDownloader.__init__ if instantiated


class OnlineMediaDownloader:
    """
    Download videos from online platforms.
    
    Phase 1: YouTube only.
    Phase 2+: Multi-platform support.
    """
    
    def __init__(
        self,
        cache_dir: Path = Path("in/online"),
        format_quality: str = "best",
        audio_only: bool = False,
        youtube_username: Optional[str] = None,
        youtube_password: Optional[str] = None
    ):
        """
        Initialize online media downloader.
        
        Args:
            cache_dir: Directory to store downloaded videos
            format_quality: Video quality ('best', '1080p', '720p', '480p', 'audio')
            audio_only: Download audio only (for transcribe/translate workflows)
            youtube_username: YouTube Premium username/email (optional)
            youtube_password: YouTube Premium password (optional)
        
        Example:
            >>> downloader = OnlineMediaDownloader()
            >>> local_path = downloader.download("https://youtube.com/watch?v=VIDEO_ID")
            
            >>> # With YouTube Premium
            >>> downloader = OnlineMediaDownloader(
            ...     youtube_username="user@gmail.com",
            ...     youtube_password="password"
            ... )
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.format_quality = format_quality
        self.audio_only = audio_only
        self.youtube_username = youtube_username
        self.youtube_password = youtube_password
        
        if not YT_DLP_AVAILABLE:
            raise ImportError(
                "yt-dlp not installed. Install with:\n"
                "  pip install -r requirements/requirements-youtube.txt"
            )
    
    def is_url(self, media_path: str) -> bool:
        """
        Check if media path is a URL.
        
        Args:
            media_path: Media path or URL
            
        Returns:
            True if URL, False if local path
            
        Example:
            >>> downloader.is_url("https://youtube.com/watch?v=VIDEO_ID")
            True
            >>> downloader.is_url("in/movie.mp4")
            False
        """
        try:
            result = urlparse(media_path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def is_youtube_url(self, url: str) -> bool:
        """
        Check if URL is a YouTube video.
        
        Args:
            url: URL to check
            
        Returns:
            True if YouTube URL, False otherwise
            
        Example:
            >>> downloader.is_youtube_url("https://youtube.com/watch?v=VIDEO_ID")
            True
            >>> downloader.is_youtube_url("https://vimeo.com/12345")
            False
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        
        return False
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None if not found
            
        Example:
            >>> downloader.extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")
            'dQw4w9WgXcQ'
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def sanitize_filename(self, filename: str, max_length: int = 35) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Rules:
        - Only alphabets, numbers, and underscores allowed
        - Spaces replaced with underscores
        - All special characters removed
        - Truncated to max_length characters
        
        Args:
            filename: Original filename
            max_length: Maximum length (default: 35)
            
        Returns:
            Sanitized filename
            
        Example:
            >>> downloader.sanitize_filename("Video: Title! (2024)", max_length=35)
            'Video_Title_2024'
            >>> downloader.sanitize_filename("Hello World Test")
            'Hello_World_Test'
        """
        # Remove all special characters except spaces, letters, numbers
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', filename)
        
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        
        # Ensure not empty
        if not sanitized:
            sanitized = "video"
        
        return sanitized
    
    def get_cached_video(self, video_id: str) -> Optional[Path]:
        """
        Check if video already downloaded in cache.
        
        Looks for files with either:
        - Video ID as filename: {video_id}.ext
        - Video ID suffix: *_{video_id}.ext
        - Any file containing the video ID
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to cached video or None if not found
            
        Example:
            >>> cached = downloader.get_cached_video("dQw4w9WgXcQ")
            >>> if cached:
            ...     print(f"Using cached: {cached}")
        """
        # Pattern 1: Exact video ID match (video_id.ext)
        for ext in ['.mp4', '.mkv', '.webm', '.wav', '.m4a']:
            exact_match = self.cache_dir / f"{video_id}{ext}"
            if exact_match.exists():
                logger.info(f"✅ Found cached video: {exact_match.name}")
                return exact_match
        
        # Pattern 2: Video ID suffix (*_{video_id}.ext)
        for ext in ['.mp4', '.mkv', '.webm', '.wav', '.m4a']:
            pattern = f"*_{video_id}{ext}"
            matches = list(self.cache_dir.glob(pattern))
            if matches:
                logger.info(f"✅ Found cached video: {matches[0].name}")
                return matches[0]
        
        # Pattern 3: Video ID anywhere in filename (fallback)
        patterns = [f"*{video_id}*"]
        for pattern in patterns:
            matches = list(self.cache_dir.glob(pattern))
            if matches:
                # Return first match
                logger.info(f"✅ Found cached video: {matches[0].name}")
                return matches[0]
        
        return None
    
    def _get_format_selector(self) -> str:
        """
        Get yt-dlp format selector based on quality setting.
        
        Returns:
            Format selector string for yt-dlp
        """
        if self.audio_only or self.format_quality == 'audio':
            # Best audio only
            return 'bestaudio/best'
        
        quality_map = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        }
        
        return quality_map.get(self.format_quality, 'bestvideo+bestaudio/best')
    
    def download(
        self,
        url: str,
        output_filename: Optional[str] = None,
        use_title_as_filename: bool = True
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Download video from URL.
        
        Args:
            url: Video URL (YouTube only in Phase 1)
            output_filename: Custom output filename (optional)
            use_title_as_filename: Use video title as filename instead of video ID (default: True)
            
        Returns:
            Tuple of (local_path, metadata)
            
        Raises:
            ValueError: If URL is not supported
            RuntimeError: If download fails
            
        Example:
            >>> downloader = OnlineMediaDownloader()
            >>> path, metadata = downloader.download("https://youtube.com/watch?v=VIDEO_ID")
            >>> print(f"Downloaded: {path}")
            >>> print(f"Title: {metadata['title']}")
            
            >>> # Use video ID as filename
            >>> path, metadata = downloader.download(url, use_title_as_filename=False)
        """
        # Validate URL
        if not self.is_url(url):
            raise ValueError(f"Not a valid URL: {url}")
        
        # Phase 1: YouTube only
        if not self.is_youtube_url(url):
            raise ValueError(
                f"Only YouTube URLs supported in Phase 1.\n"
                f"URL: {url}\n"
                f"Future phases will support more platforms."
            )
        
        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        logger.info(f"📹 YouTube video ID: {video_id}")
        
        # Check cache
        cached_video = self.get_cached_video(video_id)
        if cached_video:
            logger.info(f"♻️  Using cached video (skip download)")
            
            # Extract metadata from cached file
            metadata = self._extract_metadata(cached_video)
            return cached_video, metadata
        
        # Download video
        logger.info(f"⬇️  Downloading from YouTube...")
        logger.info(f"   URL: {url}")
        logger.info(f"   Quality: {self.format_quality}")
        
        # Check if YouTube Premium credentials provided
        if self.youtube_username:
            logger.info(f"   Authentication: YouTube Premium (user: {self.youtube_username})")
        
        # Prepare yt-dlp options
        ydl_opts = {
            'format': self._get_format_selector(),
            'outtmpl': str(self.cache_dir / f'{video_id}.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }] if not self.audio_only else [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        
        # Add YouTube Premium authentication if provided
        if self.youtube_username and self.youtube_password:
            ydl_opts['username'] = self.youtube_username
            ydl_opts['password'] = self.youtube_password
            logger.info("   Using YouTube Premium credentials")
        elif self.youtube_username or self.youtube_password:
            logger.warning("⚠️  YouTube Premium credentials incomplete (need both username and password)")
        
        # Download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get title
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', video_id)
                
                # Determine final filename
                if output_filename:
                    final_filename = output_filename
                elif use_title_as_filename:
                    # Use format: {sanitized_title}_{video_id}.ext
                    # sanitized_title: max 35 chars, only alphanumeric + underscore
                    sanitized_title = self.sanitize_filename(video_title, max_length=35)
                    final_filename = f"{sanitized_title}_{video_id}.mp4"
                    if self.audio_only:
                        final_filename = f"{sanitized_title}_{video_id}.wav"
                else:
                    # Use video ID only as filename
                    final_filename = f"{video_id}.mp4"
                    if self.audio_only:
                        final_filename = f"{video_id}.wav"
                
                logger.info(f"   Target filename: {final_filename}")
                
                # Update output template to use determined filename
                ydl_opts['outtmpl'] = str(self.cache_dir / '%(id)s.%(ext)s')
                
                # Now download with updated options
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=True)
                
                # Get downloaded file path (yt-dlp uses video_id.ext by default)
                downloaded_file = self.cache_dir / f"{video_id}.mp4"
                if self.audio_only:
                    downloaded_file = self.cache_dir / f"{video_id}.wav"
                
                # Rename to final filename if different
                final_path = self.cache_dir / final_filename
                if downloaded_file != final_path and downloaded_file.exists():
                    logger.info(f"   Renaming: {downloaded_file.name} → {final_filename}")
                    downloaded_file.rename(final_path)
                    downloaded_file = final_path
                
                # Build metadata
                metadata = {
                    'video_id': video_id,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', ''),
                    'url': url,
                }
                
                logger.info(f"✅ Download complete: {downloaded_file.name}")
                logger.info(f"   Title: {metadata['title']}")
                logger.info(f"   Duration: {metadata['duration']}s")
                
                return downloaded_file, metadata
                
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"❌ Download failed: {e}", exc_info=True)
            raise RuntimeError(f"YouTube download failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            raise RuntimeError(f"Download failed: {e}")
    
    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        Progress callback for yt-dlp.
        
        Args:
            d: Progress dict from yt-dlp
        """
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            logger.info(f"   Progress: {percent} | Speed: {speed} | ETA: {eta}")
        elif d['status'] == 'finished':
            logger.info(f"   Download finished, processing...")
    
    def _extract_metadata(self, video_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from cached video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Metadata dict
        """
        # For cached files, return minimal metadata
        return {
            'video_id': video_path.stem,
            'title': video_path.stem,
            'duration': 0,
            'uploader': 'Unknown',
            'upload_date': 'Unknown',
            'view_count': 0,
            'description': '',
            'url': '',
            'cached': True
        }


def load_youtube_credentials(user_id: int = 1) -> tuple[Optional[str], Optional[str]]:
    """
    Load YouTube Premium credentials from user profile.
    
    Args:
        user_id: User ID (default: 1)
        
    Returns:
        Tuple of (username, password) or (None, None) if not configured
        
    Example:
        >>> username, password = load_youtube_credentials(user_id=1)
        >>> if username:
        ...     downloader = OnlineMediaDownloader(
        ...         youtube_username=username,
        ...         youtube_password=password
        ...     )
    """
    try:
        from shared.user_profile import UserProfile
        profile = UserProfile.load(user_id)
        
        # Check if YouTube Premium is enabled
        if not profile.has_service('youtube'):
            return None, None
        
        youtube_config = profile.data.get('online_services', {}).get('youtube', {})
        premium_config = youtube_config.get('premium', {})
        
        if not premium_config.get('enabled', False):
            return None, None
        
        username = premium_config.get('username', '')
        password = premium_config.get('password', '')
        
        if username and password:
            logger.info(f"✅ Loaded YouTube Premium credentials for user {user_id}")
            return username, password
        else:
            logger.warning(f"⚠️  YouTube Premium enabled but credentials missing for user {user_id}")
            return None, None
            
    except Exception as e:
        logger.warning(f"⚠️  Could not load YouTube Premium credentials: {e}")
        return None, None


# ════════════════════════════════════════════════════════════════════════════
# PLAYLIST SUPPORT (Week 4 Feature 3)
# ════════════════════════════════════════════════════════════════════════════

def is_playlist_url(url: str) -> bool:
    """
    Check if URL is a YouTube playlist.
    
    Args:
        url: YouTube URL
        
    Returns:
        True if playlist URL, False otherwise
        
    Example:
        >>> is_playlist_url("https://youtube.com/playlist?list=PLxxx")
        True
        >>> is_playlist_url("https://youtube.com/watch?v=abc123")
        False
    """
    return 'playlist' in url or ('list=' in url and 'watch' not in url)


def get_playlist_info(playlist_url: str) -> Dict[str, Any]:
    """
    Get playlist metadata without downloading videos.
    
    Args:
        playlist_url: YouTube playlist URL
        
    Returns:
        Dict with title, video_count, videos (list of dicts)
        
    Example:
        >>> info = get_playlist_info("https://youtube.com/playlist?list=PLxxx")
        >>> print(f"Playlist: {info['title']} ({info['video_count']} videos)")
    """
    if not YT_DLP_AVAILABLE:
        logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
        return {"title": "Unknown", "video_count": 0, "videos": []}
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just extract info
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            
            videos = []
            for entry in info.get('entries', []):
                if entry:  # Some entries may be None
                    videos.append({
                        'video_id': entry.get('id', ''),
                        'title': entry.get('title', 'Unknown'),
                        'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Unknown')
                    })
            
            return {
                'title': info.get('title', 'Unknown Playlist'),
                'video_count': len(videos),
                'videos': videos
            }
            
    except Exception as e:
        logger.error(f"Failed to parse playlist: {e}")
        return {"title": "Unknown", "video_count": 0, "videos": []}


def format_playlist_summary(playlist_info: Dict[str, Any]) -> str:
    """
    Format playlist information for display.
    
    Args:
        playlist_info: Dict from get_playlist_info()
        
    Returns:
        Formatted string for display
    """
    title = playlist_info.get('title', 'Unknown')
    video_count = playlist_info.get('video_count', 0)
    videos = playlist_info.get('videos', [])
    
    lines = []
    lines.append(f"\n📺 Playlist: {title}")
    lines.append(f"📋 Videos: {video_count}")
    lines.append("")
    
    # Show first 5 videos as preview
    for i, video in enumerate(videos[:5], 1):
        duration_min = video.get('duration', 0) / 60
        lines.append(f"  {i}. {video['title']} ({duration_min:.1f} min)")
    
    if video_count > 5:
        lines.append(f"  ... and {video_count - 5} more")
    
    return "\n".join(lines)


def is_online_url(media_path: str) -> bool:
    """
    Check if media path is an online URL.
    
    Convenience function for scripts.
    
    Args:
        media_path: Media path or URL
        
    Returns:
        True if URL, False if local path
        
    Example:
        >>> from shared.online_downloader import is_online_url
        >>> if is_online_url(media_path):
        ...     # Download first
        ...     downloader = OnlineMediaDownloader()
        ...     local_path, metadata = downloader.download(media_path)
        ... else:
        ...     # Use local path directly
        ...     local_path = Path(media_path)
    """
    try:
        result = urlparse(media_path)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


if __name__ == "__main__":
    # CLI entry point for testing
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download videos from online platforms (YouTube Phase 1)"
    )
    parser.add_argument(
        "url",
        help="Video URL (YouTube only in Phase 1)"
    )
    parser.add_argument(
        "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p", "audio"],
        help="Video quality (default: best)"
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only"
    )
    parser.add_argument(
        "--cache-dir",
        default="in/online",
        help="Cache directory (default: in/online)"
    )
    parser.add_argument(
        "--use-video-id",
        action="store_true",
        help="Use video ID as filename instead of title"
    )
    
    args = parser.parse_args()
    
    try:
        downloader = OnlineMediaDownloader(
            cache_dir=Path(args.cache_dir),
            format_quality=args.quality,
            audio_only=args.audio_only
        )
        
        local_path, metadata = downloader.download(
            args.url,
            use_title_as_filename=not args.use_video_id
        )
        
        print(f"\n✅ Success!")
        print(f"   Local path: {local_path}")
        print(f"   Title: {metadata['title']}")
        print(f"   Duration: {metadata['duration']}s")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
