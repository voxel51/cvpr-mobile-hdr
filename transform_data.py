import multiprocessing
import os
from pathlib import Path

import cv2
import imageio
import numpy as np

WHITE_BALANCING_STRATEGY_GRAYWORLD = "grayworld"
WHITE_BALANCING_STRATEGY_NONE = "none"


def convert_raw_to_srgb(raw_data, gamma_factor, white_balancing_strategy):
    """
    This function converts the raw data to an sRGB image.
    """

    # if raw data is in the shape of (4, H, W) or (8, H, W), transpose it to (H, W, 4) or (H, W, 8)
    if raw_data.shape[0] <= 8:
        raw_data = np.transpose(raw_data, (1, 2, 0))

    # extract the Bayer pattern channels from the raw data
    b_raw, g1_raw, g2_raw, r_raw = (
        raw_data[..., 0],
        raw_data[..., 1],
        raw_data[..., 2],
        raw_data[..., 3],
    )

    if white_balancing_strategy == WHITE_BALANCING_STRATEGY_GRAYWORLD:
        # apply gray-world white-balancing.
        # compute average intensity for each channel
        avg_r = np.mean(r_raw)
        avg_g1 = np.mean(g1_raw)
        avg_g2 = np.mean(g2_raw)
        avg_b = np.mean(b_raw)
        # since there're two G in bayer filtering, this represents average green channel value
        avg_g = (avg_g1 + avg_g2) / 2

        # compute scaling factors for red and blue channels
        r_scale = avg_g / avg_r
        b_scale = avg_g / avg_b

        # scale red and blue channels using computed factors
        r_raw *= r_scale
        b_raw *= b_scale
    elif white_balancing_strategy == WHITE_BALANCING_STRATEGY_NONE:
        pass
    else:
        raise (f"unrecognized white balancing strategy: {white_balancing_strategy}")

    # dimensions of raw data
    h, w = g1_raw.shape

    # create an empty Bayer pattern image that will hold the modified color channels
    # dimensions are doubled as each channel will fit into their respective bayer pattern locations
    bayer_img = np.zeros((h * 2, w * 2), dtype=np.float32)

    # assign the extracted channels to their respective Bayer pattern locations
    bayer_img[1::2, 1::2] = r_raw
    bayer_img[::2, 1::2] = g2_raw
    bayer_img[1::2, ::2] = g1_raw
    bayer_img[::2, ::2] = b_raw

    # convert the Bayer pattern image to a 3-channel RGB image
    # bayer image values are scaled to 16-but before conversion
    rgb_image = cv2.cvtColor(
        (65535 * bayer_img).astype(np.uint16), cv2.COLOR_BAYER_RG2BGR
    )

    # normalize the RGB image to [0, 1] range
    scaled_image = rgb_image / 65535.0

    # apply gamma correction
    gamma_corrected_image = np.power(scaled_image, 1.0 / gamma_factor)

    # scale the gamma-corrected image to [0, 255] range and convert to an 8-bit unsigned integer
    srgb_image = (gamma_corrected_image * 255).astype(np.uint8)

    return srgb_image


def convert_npz_to_pngs(npz_file, output_path, gamma_factor, white_balancing_strategy):
    """
    This function processes the NPZ file and saves the sRGB images.
    """

    print("processing", npz_file)

    data = np.load(npz_file)
    keys = ["sht", "mid", "lng", "hdr"]

    for key in keys:
        if data[key].shape[0] == 4:
            raw_data = data[key][:4]
        else:
            raw_data = data[key][4:]

        # Create a subfolder for the key
        key_folder = os.path.join(output_path, key)
        os.makedirs(key_folder, exist_ok=True)

        # Process the raw data to obtain an sRGB image
        try:
            srgb_image = convert_raw_to_srgb(
                raw_data, gamma_factor, white_balancing_strategy
            )
            output_file = os.path.join(
                key_folder,
                f"{os.path.basename(npz_file).replace('.npz', '')}_wb_{white_balancing_strategy}.png",
            )
            imageio.imwrite(output_file, np.clip(srgb_image, 0, 255).astype(np.uint8))
            print(f"wrote {output_file}")
        except Exception as e:
            print(f"couldn't process {npz_file}")
            print(e)


def main():
    root_dir = Path("Mobile-HDR/NPZ_data")
    output_dir = Path("Mobile-HDR/PNG_data")

    # Create a multiprocessing pool
    pool = multiprocessing.Pool()

    try:
        npz_files = list(root_dir.glob("**/*.npz"))

        for npz_file_path in npz_files:
            output_path = output_dir / npz_file_path.relative_to(root_dir).parent
            output_path.mkdir(parents=True, exist_ok=True)

            pool.apply_async(
                convert_npz_to_pngs,
                (npz_file_path, output_path, 2.2, WHITE_BALANCING_STRATEGY_GRAYWORLD),
            )
            pool.apply_async(
                convert_npz_to_pngs,
                (npz_file_path, output_path, 2.2, WHITE_BALANCING_STRATEGY_NONE),
            )

        pool.close()

        # wait for all tasks to complete
        pool.join()

    except KeyboardInterrupt:
        print("Ctrl+C detected. Cancelling remaining tasks...")
        pool.terminate()


if __name__ == "__main__":
    main()
