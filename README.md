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

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install imagemagick ffmpeg libimage-exiftool-perl
```

#### macOS
```bash
brew install imagemagick ffmpeg exiftool
```

## Installation

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

To download a tour and convert all skybox images to equirectangular format:

```bash
python matterport_dl.py YywKFx36u6z
```

### Advanced Usage

1. Download and convert with specific width:
```bash
python matterport_dl.py YywKFx36u6z --width 4096
```

2. Only convert existing downloaded files (skip download):
```bash
python matterport_dl.py YywKFx36u6z --convert-only
```

## Output Structure

The script creates a directory structure like this:

```
tours/
└── YywKFx36u6z/
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
