import subprocess
from pathlib import Path
import tempfile
import os
import random
import string
import platform


def is_windows():
    """Check if running on Windows."""
    return platform.system().lower() == "windows"


def generate_temp_filename(prefix="skyequi-tmp", suffix=".bmp"):
    """Generate a random temporary filename."""
    random_str = "".join(random.choices(string.digits, k=10))
    return f"{prefix}{random_str}{suffix}"


def convert_skybox_to_equirectangular(
    front, back, right, left, top, bottom, output, width=None, scale_percent=100
):
    """
    Convert 6 skybox images to equirectangular format using montage, ffmpeg, and exiftool.

    Args:
        front, back, right, left, top, bottom: Paths to the skybox images
        output: Path for the output equirectangular image
        width: Optional width for the output image. If not provided, uses 4x the width of input images.
        scale_percent: Scale percentage for the final image (1-100). Default is 100 (no scaling).
    """
    # Check if output already exists
    if Path(output).exists():
        print(f"{output} already exists")
        return False

    # Create temporary files with windows-safe random names
    temp_montage = Path(tempfile.gettempdir()) / generate_temp_filename(suffix=".bmp")
    temp_ffmpeg = Path(tempfile.gettempdir()) / generate_temp_filename(suffix=".bmp")
    temp_jpg = Path(tempfile.gettempdir()) / generate_temp_filename(suffix=".jpg")
    temp_scaled = Path(tempfile.gettempdir()) / generate_temp_filename(suffix=".jpg")

    try:
        # Run montage to combine images
        print("Running montage...")
        montage_cmd = ["magick", "montage"] if is_windows() else ["montage"]
        montage_cmd.extend(
            [
                str(left),
                str(right),
                str(top),
                str(bottom),
                str(front),
                str(back),
                "-tile",
                "6x1",
                "-geometry",
                "x+0+0",
                str(temp_montage),
            ]
        )
        subprocess.run(montage_cmd, check=True, capture_output=True)

        # Determine output dimensions
        if not width:
            # Get input image width using ffprobe
            probe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(front),
            ]
            width = (
                int(
                    subprocess.check_output(probe_cmd, stderr=subprocess.DEVNULL)
                    .decode()
                    .strip()
                )
                * 4
            )
        height = width // 2

        # Run ffmpeg for conversion
        print("Running ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",  # Hide ffmpeg compilation info
            "-loglevel",
            "error",  # Only show errors
            "-i",
            str(temp_montage),
            "-vf",
            f"v360=c6x1:equirect:w={width}:h={height}",
            str(temp_ffmpeg),
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        # Convert to jpg with high quality
        print("Converting to JPG...")
        convert_cmd = ["magick", "convert"] if is_windows() else ["convert"]
        convert_cmd.extend([str(temp_ffmpeg), "-quality", "100", str(temp_jpg)])
        subprocess.run(convert_cmd, check=True, capture_output=True)

        # Scale the image if requested
        if scale_percent != 100:
            print(f"Scaling image to {scale_percent}%...")
            scale_width = int(width * scale_percent / 100)
            scale_height = int(height * scale_percent / 100)

            scale_cmd = ["magick", "convert"] if is_windows() else ["convert"]
            scale_cmd.extend(
                [
                    str(temp_jpg),
                    "-resize",
                    f"{scale_width}x{scale_height}",
                    str(temp_scaled),
                ]
            )
            subprocess.run(scale_cmd, check=True, capture_output=True)
            temp_jpg = temp_scaled  # Use the scaled image for metadata and final output
            width = scale_width
            height = scale_height

        # Add metadata with exiftool
        print("Adding metadata...")
        exiftool_cmd = [
            "exiftool",
            "-overwrite_original",
            "-q",  # Quiet mode
            "-UsePanoramaViewer=True",
            "-ProjectionType=equirectangular",
            "-PoseHeadingDegrees=180.0",
            "-CroppedAreaLeftPixels=0",
            f"-FullPanoWidthPixels={width}",
            f"-CroppedAreaImageHeightPixels={height}",
            f"-FullPanoHeightPixels={height}",
            f"-CroppedAreaImageWidthPixels={width}",
            "-CroppedAreaTopPixels=0",
            "-LargestValidInteriorRectLeft=0",
            "-LargestValidInteriorRectTop=0",
            f"-LargestValidInteriorRectWidth={width}",
            f"-LargestValidInteriorRectHeight={height}",
            "-Model=github fdd4s",
            str(temp_jpg),
        ]
        subprocess.run(exiftool_cmd, check=True, capture_output=True)

        # Move to final destination
        os.replace(temp_jpg, output)
        print(f"Created {output}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return False
    finally:
        # Clean up temporary files
        for temp_file in [temp_montage, temp_ffmpeg, temp_jpg, temp_scaled]:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_file}: {e}")
