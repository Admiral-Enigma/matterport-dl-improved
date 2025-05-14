# Matterport Tour Downloader and Converter

This script downloads Matterport virtual tour skybox images and converts them to equirectangular format. It improves upon the original workflow by:
- Downloading images in parallel (4 concurrent downloads)
- Organizing files into tour-specific folders
- Providing a simple command-line interface
- Cross-platform support (Windows, Linux, macOS)

## Prerequisites

- Python 3.6+
- ImageMagick (`montage` and `convert` commands)
- `ffmpeg` and `ffprobe`
- `exiftool`
- UV package manager (`pip install uv`)

### Installing Prerequisites

#### Windows
1. Install ImageMagick: Download from [imagemagick.org](https://imagemagick.org/script/download.php#windows)
2. Install FFmpeg: Download from [ffmpeg.org](https://ffmpeg.org/download.html#build-windows) or use winget:
   ```powershell
   winget install FFmpeg
   ```
3. Install ExifTool: Download from [exiftool.org](https://exiftool.org/) or use winget:
   ```powershell
   winget install ExifTool
   ```
4. Install UV:
   ```powershell
   pip install uv
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install imagemagick ffmpeg libimage-exiftool-perl
pip install uv
```

#### macOS
```bash
brew install imagemagick ffmpeg exiftool
pip install uv
```

## Installation

1. Clone this repository
2. Install Python dependencies using UV:
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

### Basic Usage

To download a tour and convert all skybox images to equirectangular format:

```bash
python matterport_dl.py <tour-id>
```

### Advanced Usage

1. Only convert existing downloaded files (skip download):
```bash
python matterport_dl.py <tour-id> --convert-only
```

2. Set custom width for the equirectangular image:
```bash
python matterport_dl.py <tour-id> --width 4096
```

3. Scale the final image to a percentage of original size:
```bash
python matterport_dl.py <tour-id> --scale 75  # Scale to 75% of original size
```

4. Combine options:
```bash
python matterport_dl.py <tour-id> --width 4096 --scale 50 --convert-only
```

## Output Structure

The script creates a directory structure like this:

```
tours/
└── <tour-id>/
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox0.jpg
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox1.jpg
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox2.jpg
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox3.jpg
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox4.jpg
    ├── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-skybox5.jpg
    └── equi/
        └── pan-4k-f1885b7e0a7941dd92566e74ef88dd09-equi.jpg
```

## Error Handling

- The script will retry failed downloads up to 3 times
- Existing files are skipped to allow resuming interrupted downloads
- Missing skybox images are reported but don't stop the entire process
- Temporary files are automatically cleaned up after conversion
