"""
FFmpeg Mux wrapper for native MPS pipeline.
Muxes video, audio, and subtitle streams into final output.
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil


class FFmpegMuxer:
    """
    FFmpeg muxing operations for combining video, audio, and subtitle streams.
    
    Supports:
    - Embedding SRT subtitles
    - Multiple subtitle tracks
    - Stream copying (no re-encoding)
    - Metadata preservation
    - Format selection (MP4, MKV, etc.)
    """
    
    def __init__(self, logger=None):
        """
        Initialize FFmpeg muxer.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.ffmpeg_path = self._find_ffmpeg()
        
        if self.logger:
            self.logger.info(f"FFmpeg found at: {self.ffmpeg_path}")
    
    def _find_ffmpeg(self) -> str:
        """
        Find FFmpeg executable.
        
        Returns:
            Path to FFmpeg executable
            
        Raises:
            FileNotFoundError: If FFmpeg not found
        """
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise FileNotFoundError(
                "FFmpeg not found. Please install FFmpeg: brew install ffmpeg"
            )
        return ffmpeg
    
    def get_stream_info(self, video_file: Path) -> Dict:
        """
        Get stream information from video file using ffprobe.
        
        Args:
            video_file: Path to video file
            
        Returns:
            Dictionary with stream information
        """
        ffprobe = shutil.which('ffprobe')
        if not ffprobe:
            if self.logger:
                self.logger.warning("ffprobe not found, skipping stream info")
            return {}
        
        cmd = [
            ffprobe,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_file)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            info = json.loads(result.stdout)
            
            if self.logger:
                streams = info.get('streams', [])
                self.logger.debug(f"Found {len(streams)} streams in input file")
                for i, stream in enumerate(streams):
                    codec_type = stream.get('codec_type', 'unknown')
                    codec_name = stream.get('codec_name', 'unknown')
                    self.logger.debug(f"  Stream {i}: {codec_type} ({codec_name})")
            
            return info
            
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.warning(f"Failed to get stream info: {e}")
            return {}
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.warning(f"Failed to parse stream info: {e}")
            return {}
    
    def mux_subtitles(
        self,
        video_file: Path,
        subtitle_file: Path,
        output_file: Path,
        subtitle_language: str = 'eng',
        subtitle_title: str = 'English',
        subtitle_codec: str = None,
        container_format: str = 'mp4',
        copy_video: bool = True,
        copy_audio: bool = True,
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Mux subtitle file into video container.
        
        Args:
            video_file: Input video file
            subtitle_file: SRT subtitle file
            output_file: Output video file
            subtitle_language: ISO 639-2 language code (default: 'eng')
            subtitle_title: Subtitle track title (default: 'English')
            subtitle_codec: Subtitle codec (default: auto-detect from container)
            container_format: Output container format (default: 'mp4')
            copy_video: Copy video stream without re-encoding (default: True)
            copy_audio: Copy audio stream without re-encoding (default: True)
            overwrite: Overwrite output file if exists (default: False)
            
        Returns:
            Tuple of (success, message)
        """
        if self.logger:
            self.logger.info("Preparing to mux subtitles into video")
            self.logger.debug(f"Video: {video_file}")
            self.logger.debug(f"Subtitles: {subtitle_file}")
            self.logger.debug(f"Output: {output_file}")
            self.logger.debug(f"Language: {subtitle_language}")
            self.logger.debug(f"Format: {container_format}")
            self.logger.debug(f"Copy video: {copy_video}")
            self.logger.debug(f"Copy audio: {copy_audio}")
        
        # Validate inputs
        if not video_file.exists():
            return False, f"Video file not found: {video_file}"
        
        if not subtitle_file.exists():
            return False, f"Subtitle file not found: {subtitle_file}"
        
        if output_file.exists() and not overwrite:
            return False, f"Output file exists: {output_file}"
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine codecs
        video_codec = 'copy' if copy_video else 'libx264'
        audio_codec = 'copy' if copy_audio else 'aac'
        
        # Auto-detect subtitle codec if not specified
        if subtitle_codec is None:
            if container_format.lower() == 'mp4':
                subtitle_codec = 'mov_text'
            elif container_format.lower() in ['mkv', 'matroska']:
                subtitle_codec = 'srt'
            else:
                subtitle_codec = 'mov_text'  # Default fallback
        
        # Build FFmpeg command based on container format
        if container_format.lower() == 'mp4':
            # MP4 format
            cmd = [
                self.ffmpeg_path,
                '-y' if overwrite else '-n',
                '-i', str(video_file),
                '-i', str(subtitle_file),
                '-c:v', video_codec,
                '-c:a', audio_codec,
                '-c:s', subtitle_codec,
                '-metadata:s:s:0', f'language={subtitle_language}',
                '-metadata:s:s:0', f'title={subtitle_title}',
                '-movflags', '+faststart',
                str(output_file)
            ]
        elif container_format.lower() in ['mkv', 'matroska']:
            # MKV format
            cmd = [
                self.ffmpeg_path,
                '-y' if overwrite else '-n',
                '-i', str(video_file),
                '-i', str(subtitle_file),
                '-c:v', video_codec,
                '-c:a', audio_codec,
                '-c:s', subtitle_codec,
                '-metadata:s:s:0', f'language={subtitle_language}',
                '-metadata:s:s:0', f'title={subtitle_title}',
                str(output_file)
            ]
        else:
            return False, f"Unsupported container format: {container_format}"
        
        if self.logger:
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            self.logger.info("Starting FFmpeg muxing process...")
        
        # Execute FFmpeg
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.logger:
                self.logger.info("FFmpeg muxing completed successfully")
                if result.stderr:
                    # FFmpeg outputs progress to stderr
                    for line in result.stderr.split('\n')[-10:]:
                        if line.strip():
                            self.logger.debug(f"FFmpeg: {line.strip()}")
            
            return True, "Muxing successful"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg failed with exit code {e.returncode}"
            if self.logger:
                self.logger.error(error_msg)
                if e.stderr:
                    for line in e.stderr.split('\n')[-20:]:
                        if line.strip():
                            self.logger.error(f"FFmpeg: {line.strip()}")
            
            return False, error_msg
    
    def mux_multiple_subtitles(
        self,
        video_file: Path,
        subtitle_files: List[Dict[str, str]],
        output_file: Path,
        container_format: str = 'mkv',
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Mux multiple subtitle tracks into video.
        
        Args:
            video_file: Input video file
            subtitle_files: List of subtitle dicts with 'file', 'language', 'title'
            output_file: Output video file
            container_format: Output container (default: 'mkv' - supports multiple subs)
            overwrite: Overwrite output if exists
            
        Returns:
            Tuple of (success, message)
            
        Example:
            subtitle_files = [
                {'file': 'en.srt', 'language': 'eng', 'title': 'English'},
                {'file': 'hi.srt', 'language': 'hin', 'title': 'Hindi'}
            ]
        """
        if self.logger:
            self.logger.info(f"Muxing {len(subtitle_files)} subtitle tracks")
        
        # Validate
        if not video_file.exists():
            return False, f"Video file not found: {video_file}"
        
        for sub in subtitle_files:
            sub_file = Path(sub['file'])
            if not sub_file.exists():
                return False, f"Subtitle file not found: {sub_file}"
        
        if output_file.exists() and not overwrite:
            return False, f"Output file exists: {output_file}"
        
        # Build command
        cmd = [
            self.ffmpeg_path,
            '-y' if overwrite else '-n',
            '-i', str(video_file)
        ]
        
        # Add subtitle inputs
        for sub in subtitle_files:
            cmd.extend(['-i', str(sub['file'])])
        
        # Map streams
        cmd.extend([
            '-map', '0:v',  # Video from first input
            '-map', '0:a',  # Audio from first input
        ])
        
        # Map subtitle streams
        for i in range(len(subtitle_files)):
            cmd.extend(['-map', f'{i+1}:s'])
        
        # Copy codecs
        cmd.extend([
            '-c:v', 'copy',
            '-c:a', 'copy',
        ])
        
        # Set subtitle codec based on format
        if container_format.lower() == 'mp4':
            cmd.extend(['-c:s', 'mov_text'])
        else:  # MKV
            cmd.extend(['-c:s', 'srt'])
        
        # Add metadata for each subtitle
        for i, sub in enumerate(subtitle_files):
            lang = sub.get('language', 'und')
            title = sub.get('title', f'Subtitle {i+1}')
            cmd.extend([
                f'-metadata:s:s:{i}', f'language={lang}',
                f'-metadata:s:s:{i}', f'title={title}'
            ])
        
        cmd.append(str(output_file))
        
        if self.logger:
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.logger:
                self.logger.info("Multi-subtitle muxing completed successfully")
            
            return True, f"Muxed {len(subtitle_files)} subtitle tracks"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg failed with exit code {e.returncode}"
            if self.logger:
                self.logger.error(error_msg)
                if e.stderr:
                    for line in e.stderr.split('\n')[-20:]:
                        if line.strip():
                            self.logger.error(f"FFmpeg: {line.strip()}")
            
            return False, error_msg
    
    def add_metadata(
        self,
        video_file: Path,
        output_file: Path,
        metadata: Dict[str, str],
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Add metadata to video file.
        
        Args:
            video_file: Input video file
            output_file: Output video file
            metadata: Dictionary of metadata key-value pairs
            overwrite: Overwrite output if exists
            
        Returns:
            Tuple of (success, message)
            
        Example:
            metadata = {
                'title': 'Movie Title',
                'year': '2008',
                'genre': 'Drama',
                'comment': 'Processed with native pipeline'
            }
        """
        if self.logger:
            self.logger.info("Adding metadata to video")
            for key, value in metadata.items():
                self.logger.debug(f"  {key}: {value}")
        
        # Validate
        if not video_file.exists():
            return False, f"Video file not found: {video_file}"
        
        if output_file.exists() and not overwrite:
            return False, f"Output file exists: {output_file}"
        
        # Build command
        cmd = [
            self.ffmpeg_path,
            '-y' if overwrite else '-n',
            '-i', str(video_file),
            '-c', 'copy',  # Copy all streams
        ]
        
        # Add metadata
        for key, value in metadata.items():
            cmd.extend(['-metadata', f'{key}={value}'])
        
        cmd.append(str(output_file))
        
        if self.logger:
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Execute
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.logger:
                self.logger.info("Metadata added successfully")
            
            return True, "Metadata added"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg failed with exit code {e.returncode}"
            if self.logger:
                self.logger.error(error_msg)
            
            return False, error_msg
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        if file_path.exists():
            return file_path.stat().st_size
        return 0
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
