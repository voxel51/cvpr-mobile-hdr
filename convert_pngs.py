from PIL import Image
from pathlib import Path
import argparse


def convert_png_to_jpg(png_folder, jpg_folder, quality=70):
    png_path = Path(png_folder)
    jpg_path = Path(jpg_folder)

    # Create the output folder if it doesn't exist
    jpg_path.mkdir(parents=True, exist_ok=True)

    # Get a list of all PNG files in the input folder and its subdirectories
    png_files = png_path.rglob("*.png")

    for png_file in png_files:
        print("Converting", png_file)
        # Open the PNG image
        img = Image.open(png_file)

        # Get the relative path of the PNG file
        rel_path = png_file.relative_to(png_path)

        # Convert PNG to JPEG with specified quality
        jpg_file = rel_path.with_suffix(".jpg")
        jpg_file_path = jpg_path / jpg_file

        # Create parent directories if they don't exist
        jpg_file_path.parent.mkdir(parents=True, exist_ok=True)

        img.convert("RGB").save(jpg_file_path, "JPEG", quality=quality)

        # Close the image
        img.close()

    print("Conversion complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a folder of PNG images to JPEG format."
    )
    parser.add_argument(
        "png_folder", help="Path to the folder containing the PNG images",
        default="Mobile-HDR/PNG_data"
    )
    parser.add_argument(
        "jpg_folder", help="Path to the output folder for the converted JPEG images",
        default="Mobile-HDR/JPG_data"
    )
    parser.add_argument(
        "--quality", type=int, default=70, help="JPEG quality (0-100), default is 70"
    )
    args = parser.parse_args()

    convert_png_to_jpg(args.png_folder, args.jpg_folder, args.quality)
