#!/usr/bin/env python3
import os
import json
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import time
from converter import convert_skybox_to_equirectangular


class MatterportDownloader:
    def __init__(self, tour_id):
        self.tour_id = tour_id
        self.referer = f"https://my.matterport.com/show/?m={tour_id}"
        self.base_url = self._get_base_url()

    def _get_base_url(self):
        url = f"https://my.matterport.com/api/player/models/{self.tour_id}/files?type=3"
        headers = {
            "Referer": self.referer,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Cookie": "mp_mixpanel__c=0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data["templates"][0]

    def _get_catalog(self):
        url = self.base_url.replace("{{filename}}", "catalog.json")
        headers = {
            "Referer": self.referer,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Cookie": "mp_mixpanel__c=0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data["files"]

    def _get_skybox_resolution(self, catalog):
        for item in catalog:
            if (
                "/4k/" in item
                and "jpg" in item
                and "skybox" in item
                and not any(x in item for x in ["dds", "zip", "lased"])
            ):
                return "/4k/"

        for item in catalog:
            if (
                "/2k/" in item
                and "jpg" in item
                and "skybox" in item
                and not any(x in item for x in ["dds", "zip", "lased"])
            ):
                return "/2k/"

        return "/high/"

    def _download_file(self, file_path):
        url = self.base_url.replace("{{filename}}", file_path)
        local_filename = file_path.replace("/", "-").replace("_", "-")

        # Create tour directory
        output_dir = Path(f"tours/{self.tour_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        local_path = output_dir / local_filename

        if local_path.exists() and local_path.stat().st_size > 0:
            print(f"Skipping {local_filename} - already exists")
            return local_path

        headers = {
            "Referer": self.referer,
            "Accept": "image/png,image/*;q=0.8,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.5",
            "origin": "https://my.matterport.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        }

        for _ in range(3):  # Try up to 3 times
            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()

                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded {local_filename}")
                return local_path
            except Exception as e:
                print(f"Error downloading {local_filename}: {e}")
                if local_path.exists():
                    local_path.unlink()
                time.sleep(1)

        raise Exception(f"Failed to download {local_filename} after 3 attempts")

    def download_tour(self):
        catalog = self._get_catalog()
        resolution = self._get_skybox_resolution(catalog)

        skybox_files = [
            item
            for item in catalog
            if resolution in item
            and "jpg" in item
            and "skybox" in item
            and not any(x in item for x in ["dds", "zip", "lased"])
        ]

        if not skybox_files:
            raise Exception("No skybox files found in catalog")

        print(f"Found {len(skybox_files)} skybox files to download")

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self._download_file, skybox_files))

        return results


def convert_to_equirectangular(tour_id, width=None, scale=100):
    tour_dir = Path(f"tours/{tour_id}")
    if not tour_dir.exists():
        raise Exception(f"Tour directory {tour_dir} does not exist")

    # Create equi subfolder
    equi_dir = tour_dir / "equi"
    equi_dir.mkdir(exist_ok=True)

    # Get all unique base names for skybox sets
    skybox_files = list(tour_dir.glob("*skybox*.jpg"))
    base_names = set()
    for file in skybox_files:
        base_name = file.name.rsplit("skybox", 1)[0]
        base_names.add(base_name)

    for base_name in base_names:
        # Construct paths for all 6 skybox images
        skybox_images = []
        for i in range(6):
            img_path = tour_dir / f"{base_name}skybox{i}.jpg"
            if not img_path.exists():
                print(f"Missing skybox image: {img_path}")
                break
            skybox_images.append(str(img_path))

        if len(skybox_images) != 6:
            continue

        # Create output filename in equi subfolder
        output_file = equi_dir / f"{base_name}equi.jpg"
        if output_file.exists():
            print(f"Skipping {output_file.name} - already exists")
            continue

        print(f"Converting {base_name} to equirectangular...")
        # Order: front, back, right, left, top, bottom
        order = [1, 3, 4, 2, 0, 5]  # Reorder skybox images as required
        ordered_images = [skybox_images[i] for i in order]

        try:
            convert_skybox_to_equirectangular(
                front=ordered_images[0],
                back=ordered_images[1],
                right=ordered_images[2],
                left=ordered_images[3],
                top=ordered_images[4],
                bottom=ordered_images[5],
                output=str(output_file),
                width=width,
                scale_percent=scale,
            )
        except Exception as e:
            print(f"Error converting {base_name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Download and convert Matterport virtual tours"
    )
    parser.add_argument("tour_id", help="Matterport tour ID")
    parser.add_argument(
        "--width", type=int, help="Width of output equirectangular image"
    )
    parser.add_argument(
        "--scale",
        type=int,
        choices=range(1, 101),
        metavar="1-100",
        help="Scale the final image to this percentage of original size",
    )
    parser.add_argument(
        "--convert-only",
        action="store_true",
        help="Skip download and only convert existing files",
    )

    args = parser.parse_args()

    if not args.convert_only:
        downloader = MatterportDownloader(args.tour_id)
        try:
            downloader.download_tour()
        except Exception as e:
            print(f"Error downloading tour: {e}")
            return

    convert_to_equirectangular(args.tour_id, args.width, args.scale)


if __name__ == "__main__":
    main()
