import numpy as np
import os
from PIL import Image
import hashlib
import matplotlib.pyplot as plt  # type: ignore #
import matplotlib.patches as patches  # type: ignore #


def data_to_colour(data):
    if isinstance(data, str):
        data = bytes(data, "utf-8")
    else:
        data = bytes(data)
    m = hashlib.sha256()
    m.update(data)
    key = int(m.hexdigest()[:8], 16)
    r = ((((key >> 0) & 0xFF) + 1) * 33) % 255
    g = ((((key >> 8) & 0xFF) + 1) * 33) % 255
    b = ((((key >> 16) & 0xFF) + 1) * 33) % 255

    # illumination normalization to 128
    inv_norm_i = 128 * (3.0 / (r + g + b))

    return (int(r * inv_norm_i) / 255, int(g * inv_norm_i) / 255, int(b * inv_norm_i) / 255)


def colorize_bbox_2d(rgb_path, data, id_to_labels, file_path):

    rgb_img = Image.open(rgb_path)
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(rgb_img)
    for bbox_2d in data:
        id = bbox_2d["semanticId"]
        color = data_to_colour(id)
        labels = id_to_labels[str(id)]
        rect = patches.Rectangle(
            xy=(bbox_2d["x_min"], bbox_2d["y_min"]),
            width=bbox_2d["x_max"] - bbox_2d["x_min"],
            height=bbox_2d["y_max"] - bbox_2d["y_min"],
            edgecolor=color,
            linewidth=2,
            label=labels,
            fill=False,
        )
        ax.add_patch(rect)

    plt.legend(loc="upper left")

    plt.savefig(file_path)


def colorize_depth(depth_data):
    near = 0.01
    far = 100
    depth_data = np.clip(depth_data, near, far)
    # depth_data = depth_data / far
    depth_data = (np.log(depth_data) - np.log(near)) / (np.log(far) - np.log(near))
    # depth_data = depth_data / far
    depth_data = 1.0 - depth_data

    depth_data_uint8 = (depth_data * 255).astype(np.uint8)

    return Image.fromarray(depth_data_uint8)

output_dir = "C:/Users/gliacloud/Documents/GliaCloud-Omniverse/exts/omni.comfyui.connector.core-0.1.0/data/replicator"
vis_out_dir = "C:/Users/gliacloud/Documents/GliaCloud-Omniverse/exts/omni.comfyui.connector.core-0.1.0/data/rep_vis"

if not os.path.exists(vis_out_dir):
    os.makedirs(vis_out_dir)

rgb = "rgb_0000.png"  # to be changed by you
rgb_path = os.path.join(output_dir, rgb)
rgb_image = Image.open(rgb_path)

distance_to_camera_file_name = "distance_to_camera_0000.npy"
distance_to_camera_data = np.load(os.path.join(output_dir, distance_to_camera_file_name))
distance_to_camera_file_name = np.nan_to_num(distance_to_camera_data, posinf=0)

distance_to_camera_image = colorize_depth(distance_to_camera_data)
distance_to_camera_image.save(os.path.join(vis_out_dir, "distance_to_camera_0000.png"))
