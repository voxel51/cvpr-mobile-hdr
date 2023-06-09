import os
import glob
import numpy as np
import cv2
import shutil
import rawpy
import imageio
import tempfile
import matplotlib.pyplot as plt
%matplotlib inline

def process_image(raw_data):
    if raw_data.shape[0] <= 8:
        raw_data = np.transpose(raw_data, (1, 2, 0))

    # extract the Bayer pattern channels from the raw data
    b_raw, g1_raw, g2_raw, r_raw = raw_data[..., 0], raw_data[..., 1], raw_data[..., 2], raw_data[..., 3]

    # gray-world white-balancing.
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
    rgb_image = cv2.cvtColor((65535 * bayer_img).astype(np.uint16), cv2.COLOR_BAYER_RG2BGR)

    # normalize the RGB image to [0, 1] range
    scaled_image = rgb_image / 65535.0

    # apply gamma correction
    gamma_corrected_image = np.power(scaled_image, 1.0 / 2.2)

    # scale the gamma-corrected image to [0, 255] range and convert to an 8-bit unsigned integer
    srgb_image = (gamma_corrected_image * 255).astype(np.uint8)

    return srgb_image

def process_and_save_npz(npz_file, output_path):
    data = np.load(npz_file)
    keys = ['sht', 'mid', 'lng', 'hdr']

    for key in keys:
        if data[key].shape[0] == 4:
            raw_data = data[key][:4]
        else:
            raw_data = data[key][4:]
        
        # Create a subfolder for the key
        key_folder = os.path.join(output_path, key)
        os.makedirs(key_folder, exist_ok=True)
        
        # Process the raw data to obtain an sRGB image
        srgb_image = process_image(raw_data)
        
        # Save the image in the key's folder
        output_file = os.path.join(key_folder, f"{os.path.basename(npz_file).replace('.npz', '')}.png")
        imageio.imwrite(output_file, np.clip(srgb_image, 0, 255).astype(np.uint8))

root_dir = 'data/NPZ_data'
output_dir = 'data/PNG_data'

# Empty the output_dir before running the code
shutil.rmtree(output_dir)
os.makedirs(output_dir)

total_processed = 0

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.npz'):
            npz_file_path = os.path.join(subdir, file)
            output_path = os.path.join(output_dir, subdir)
            os.makedirs(output_path, exist_ok=True)
            print(f"processing {npz_file_path}")
            try:
                process_and_save_npz(npz_file_path, output_path)
                print(f"       =====processed {npz_file_path} successfully")
                total_processed += 1
            except Exception as e:
                print(f"couldn't process {npz_file_path}, skipping")
                raise e

