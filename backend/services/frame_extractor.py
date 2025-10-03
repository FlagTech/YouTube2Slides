"""
Video frame extraction service using ffmpeg
"""
import ffmpeg
import os
from typing import List, Dict, Tuple
from pathlib import Path
from PIL import Image
import io


class FrameExtractor:
    """Extract frames from video at specified timestamps"""

    def __init__(self, output_dir: str = "./storage/frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_frame_at_timestamp(
        self,
        video_path: str,
        timestamp: float,
        output_filename: str = None,
        quality: int = 2
    ) -> str:
        """
        Extract a single frame at specific timestamp
        Args:
            video_path: Path to video file
            timestamp: Time in seconds
            output_filename: Custom output filename (optional)
            quality: JPEG quality (1-31, lower is better, 2 is recommended)
        Returns:
            Path to extracted frame
        """
        if output_filename is None:
            output_filename = f"frame_{timestamp:.2f}.jpg"

        output_path = self.output_dir / output_filename

        try:
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .filter('scale', -1, 720)  # Scale to 720p height, maintain aspect ratio
                .output(str(output_path), vframes=1, **{'q:v': quality})
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            return str(output_path)
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise Exception(f"Failed to extract frame at {timestamp}s: {error_message}")

    def extract_frames_batch(
        self,
        video_path: str,
        timestamps: List[float],
        video_id: str,
        quality: int = 2,
        resolution: str = "720",
        progress_callback=None
    ) -> List[Dict]:
        """
        Extract multiple frames at specified timestamps
        Args:
            video_path: Path to video file
            timestamps: List of timestamps in seconds
            video_id: Video identifier for naming
            quality: JPEG quality (1-31)
            resolution: Target resolution (360, 480, 720)
            progress_callback: Callback function(percent) for extraction progress
        Returns:
            List of dicts with frame info
        """
        frames = []
        resolution_map = {
            "360": 360,
            "480": 480,
            "720": 720
        }
        height = resolution_map.get(resolution, 720)
        total_frames = len(timestamps)

        for i, timestamp in enumerate(timestamps):
            try:
                output_filename = f"{video_id}_frame_{i+1:04d}_{timestamp:.2f}s.jpg"
                output_path = self.output_dir / output_filename

                (
                    ffmpeg
                    .input(video_path, ss=timestamp)
                    .filter('scale', -1, height)
                    .output(str(output_path), vframes=1, **{'q:v': quality})
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )

                # Get file size
                file_size = output_path.stat().st_size

                frames.append({
                    'index': i + 1,
                    'timestamp': timestamp,
                    'path': str(output_path),
                    'filename': output_filename,
                    'size_bytes': file_size
                })

                # Report progress
                if progress_callback:
                    percent = ((i + 1) / total_frames) * 100
                    progress_callback(percent)

            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if e.stderr else str(e)
                print(f"Warning: Failed to extract frame at {timestamp}s: {error_message}")
                continue

        return frames

    def extract_frames_with_subtitles(
        self,
        video_path: str,
        timestamps: List[float],
        subtitles: List[str],
        video_id: str,
        quality: int = 2,
        resolution: str = "720",
        progress_callback=None
    ) -> List[Dict]:
        """
        Extract frames and associate them with subtitle text
        Args:
            video_path: Path to video file
            timestamps: List of timestamps
            subtitles: List of subtitle texts corresponding to timestamps
            video_id: Video identifier
            quality: JPEG quality
            resolution: Target resolution
            progress_callback: Callback function(percent) for extraction progress
        Returns:
            List of dicts with frame and subtitle info
        """
        if len(timestamps) != len(subtitles):
            raise ValueError("Timestamps and subtitles lists must have same length")

        frames = self.extract_frames_batch(
            video_path=video_path,
            timestamps=timestamps,
            video_id=video_id,
            quality=quality,
            resolution=resolution,
            progress_callback=progress_callback
        )

        # Add subtitle text to each frame
        for i, frame in enumerate(frames):
            if i < len(subtitles):
                frame['subtitle'] = subtitles[i]

        return frames

    def compress_frame(
        self,
        image_path: str,
        quality: int = 85,
        max_width: int = 1280
    ) -> str:
        """
        Compress and optimize frame image
        Args:
            image_path: Path to image file
            quality: JPEG quality (0-100)
            max_width: Maximum width in pixels
        Returns:
            Path to compressed image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Resize if larger than max_width
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Save with optimization
                img.save(image_path, 'JPEG', quality=quality, optimize=True)

            return image_path
        except Exception as e:
            raise Exception(f"Failed to compress image: {str(e)}")

    def get_video_info(self, video_path: str) -> Dict:
        """
        Get video metadata using ffprobe
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

            duration = float(probe['format']['duration'])
            width = int(video_info['width'])
            height = int(video_info['height'])
            fps = eval(video_info['r_frame_rate'])  # Convert "30/1" to 30.0

            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
                'codec': video_info['codec_name'],
                'bit_rate': int(probe['format'].get('bit_rate', 0))
            }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

    def create_thumbnail_grid(
        self,
        frame_paths: List[str],
        output_path: str,
        columns: int = 3
    ) -> str:
        """
        Create a grid of thumbnails from multiple frames
        Args:
            frame_paths: List of frame image paths
            output_path: Output path for grid image
            columns: Number of columns in grid
        Returns:
            Path to grid image
        """
        if not frame_paths:
            raise ValueError("No frames provided")

        images = [Image.open(path) for path in frame_paths]

        # Get max dimensions
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)

        # Calculate grid dimensions
        rows = (len(images) + columns - 1) // columns
        grid_width = max_width * columns
        grid_height = max_height * rows

        # Create grid image
        grid = Image.new('RGB', (grid_width, grid_height), color='black')

        for i, img in enumerate(images):
            row = i // columns
            col = i % columns
            x = col * max_width
            y = row * max_height
            grid.paste(img, (x, y))

        grid.save(output_path, 'JPEG', quality=90)

        # Close all images
        for img in images:
            img.close()

        return output_path

    def cleanup_frames(self, video_id: str):
        """
        Delete all frames for a specific video
        """
        pattern = f"{video_id}_frame_*.jpg"
        deleted_count = 0

        for frame_file in self.output_dir.glob(pattern):
            try:
                frame_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Failed to delete {frame_file}: {e}")

        return deleted_count
