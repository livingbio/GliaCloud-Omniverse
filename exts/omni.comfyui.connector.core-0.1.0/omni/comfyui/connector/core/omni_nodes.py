import requests
import numpy as np
import torch  # type: ignore #
from PIL import Image, ImageOps
import os
from typing import Iterable
import itertools
import io
from comfy.utils import common_upscale, ProgressBar
from comfy.k_diffusion.utils import FolderOfImages


class OmniViewportFrameNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    FUNCTION = "get_current_viewport"
    CATEGORY = "Omniverse"

    def get_current_viewport(self):

        headers = {"Content-Type": "application/json"}

        url = "http://localhost:8111"
        path = "/viewport-capture/simple-capture"

        response = requests.post(f"{url}{path}", headers=headers)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}. Error: {response.text}")
            return Image.new("RGB", (1920, 1080))

        response_image_path = response.json()["output_url_path"]
        image_url = f"{url}{response_image_path}"

        image = Image.open(requests.get(image_url, stream=True).raw)
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")


def strip_path(path):
    # This leaves whitespace inside quotes and only a single "
    # thus ' ""test"' -> '"test'
    # consider path.strip(string.whitespace+"\"")
    # or weightier re.fullmatch("[\\s\"]*(.+?)[\\s\"]*", path).group(1)
    path = path.strip()
    if path.startswith('"'):
        path = path[1:]
    if path.endswith('"'):
        path = path[:-1]
    return path


def get_sorted_dir_files_from_directory(
    directory: str, skip_first_images: int = 0, select_every_nth: int = 1, extensions: Iterable = None
):
    directory = strip_path(directory)
    dir_files = os.listdir(directory)
    dir_files = sorted(dir_files)
    dir_files = [os.path.join(directory, x) for x in dir_files]
    dir_files = list(filter(lambda filepath: os.path.isfile(filepath), dir_files))
    # filter by extension, if needed
    if extensions is not None:
        extensions = list(extensions)
        new_dir_files = []
        for filepath in dir_files:
            ext = "." + filepath.split(".")[-1]
            if ext.lower() in extensions:
                new_dir_files.append(filepath)
        dir_files = new_dir_files
    # start at skip_first_images
    dir_files = dir_files[skip_first_images:]
    dir_files = dir_files[0::select_every_nth]
    return dir_files


def images_generator(
    directory: str,
    image_load_cap: int = 0,
    skip_first_images: int = 0,
    select_every_nth: int = 1,
    meta_batch=None,
    unique_id=None,
):
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory '{directory} cannot be found.")
    dir_files = get_sorted_dir_files_from_directory(
        directory, skip_first_images, select_every_nth, FolderOfImages.IMG_EXTENSIONS
    )

    if len(dir_files) == 0:
        raise FileNotFoundError(f"No files in directory '{directory}'.")
    if image_load_cap > 0:
        dir_files = dir_files[:image_load_cap]
    sizes = {}
    has_alpha = False
    for image_path in dir_files:
        i = Image.open(image_path)
        # exif_transpose can only ever rotate, but rotating can swap width/height
        i = ImageOps.exif_transpose(i)
        has_alpha |= "A" in i.getbands()
        count = sizes.get(i.size, 0)
        sizes[i.size] = count + 1
    size = max(sizes.items(), key=lambda x: x[1])[0]
    yield size[0], size[1], has_alpha
    if meta_batch is not None:
        yield min(image_load_cap, len(dir_files)) or len(dir_files)

    iformat = "RGBA" if has_alpha else "RGB"

    def load_image(file_path):

        # response_image_path = response.json()["output_url_path"]
        # image_url = f"{url}{response_image_path}"

        # image = Image.open(requests.get(image_url, stream=True).raw)
        # image = ImageOps.exif_transpose(image)
        # image = image.convert("RGB")
        # image = np.array(image).astype(np.float32) / 255.0
        # image = torch.from_numpy(image)[None,]

        i = Image.open(file_path)
        i = ImageOps.exif_transpose(i)
        i = i.convert(iformat)
        i = np.array(i, dtype=np.float32)
        # This nonsense provides a nearly 50% speedup on my system
        torch.from_numpy(i).div_(255)
        if i.shape[0] != size[1] or i.shape[1] != size[0]:
            i = torch.from_numpy(i).movedim(-1, 0).unsqueeze(0)
            i = common_upscale(i, size[0], size[1], "lanczos", "center")
            i = i.squeeze(0).movedim(0, -1).numpy()
        if has_alpha:
            i[:, :, -1] = 1 - i[:, :, -1]
        return i

    total_images = len(dir_files)
    processed_images = 0
    pbar = ProgressBar(total_images)
    images = map(load_image, dir_files)
    try:
        prev_image = next(images)
        while True:
            next_image = next(images)
            yield prev_image
            processed_images += 1
            pbar.update_absolute(processed_images, total_images)
            prev_image = next_image
    except StopIteration:
        pass
    if meta_batch is not None:
        meta_batch.inputs.pop(unique_id)
        meta_batch.has_closed_inputs = True
    if prev_image is not None:
        yield prev_image

def load_images_from_url(
    directory: str,
    image_load_cap: int = 0,
    skip_first_images: int = 0,
    select_every_nth: int = 1,
    meta_batch=None,
    unique_id=None,
):
    if meta_batch is None or unique_id not in meta_batch.inputs:
        gen = images_generator(directory, image_load_cap, skip_first_images, select_every_nth, meta_batch, unique_id)
        (width, height, has_alpha) = next(gen)
        if meta_batch is not None:
            meta_batch.inputs[unique_id] = (gen, width, height, has_alpha)
            meta_batch.total_frames = min(meta_batch.total_frames, next(gen))

    if meta_batch is not None:
        gen = itertools.islice(gen, meta_batch.frames_per_batch)
    images = torch.from_numpy(np.fromiter(gen, np.dtype((np.float32, (height, width, 3 + has_alpha)))))
    if has_alpha:
        # tensors are not continuous. Rewrite will be required if this is an issue
        masks = images[:, :, :, 3]
        images = images[:, :, :, :3]
    else:
        masks = torch.zeros((images.size(0), 64, 64), dtype=torch.float32, device="cpu")
    if len(images) == 0:
        raise FileNotFoundError(f"No images could be loaded from directory '{directory}'.")
    return images, masks, images.size(0)


class OmniViewportRecordingNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "num_frames_to_record": (
                    "INT",
                    {
                        "default": 100,
                        "min": 1,
                    },
                ),
                "renderer": (["RTX - Real-Time", "RTX - Interactive (Path Tracing)"],),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = (
        "rgb_out",
        "normals_out",
        "depth_out",
    )
    FUNCTION = "get_viewport_recording"
    CATEGORY = "Omniverse"

    def get_viewport_recording(self, num_frames_to_record, renderer):

        headers = {"Content-Type": "application/json"}

        url = "http://localhost:8111"
        path = "/viewport-capture/viewport-record"

        renderer_shortname = "realtime" if (renderer == "RTX - Real-Time") else "pathtracing"

        body = {"num_frames_to_record": num_frames_to_record, "renderer": renderer_shortname}

        response = requests.get(f"{url}{path}", headers=headers, json=body)

        if response.status_code != 200:
            error_message = response.json()["details_message"] if response.status_code == 400 else response.text
            raise ValueError(
                f"Request failed with status code {response.status_code}. Error message: {error_message}"
            )

        rgb_output = response.json()["output_paths"]["rgb"]
        rgb_data = np.load(rgb_output)
        rgb_tensor = torch.from_numpy(rgb_data)

        normals_output = response.json()["output_paths"]["normals"]
        normals_data = np.load(normals_output)
        normals_tensor = torch.from_numpy(normals_data)

        depth_output = response.json()["output_paths"]["depth"]
        depth_data = np.load(depth_output)
        depth_tensor = torch.from_numpy(depth_data)

        return (
            rgb_tensor,
            normals_tensor,
            depth_tensor,
        )

    @classmethod
    def IS_CHANGED(cls, num_frames_to_record, renderer):
        return float("NaN")


class OmniViewportDepthNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start_frame": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                    },
                ),
                "end_frame": (
                    "INT",
                    {
                        "default": 40,
                        "min": 20,
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    FUNCTION = "get_current_viewport"
    CATEGORY = "Omniverse"

    def get_current_viewport(self):

        headers = {"Content-Type": "application/json"}

        url = "http://localhost:8111"
        path = "/viewport-capture/simple-capture"

        response = requests.post(f"{url}{path}", headers=headers)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}. Error: {response.text}")
            return Image.new("RGB", (1920, 1080))

        response_image_path = response.json()["output_url_path"]
        image_url = f"{url}{response_image_path}"

        image = Image.open(requests.get(image_url, stream=True).raw)
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")


class OmniViewportSemanticSegmentationNode:
    @classmethod
    def INPUT_TYPES(cls):

        return {
            "required": {
                "start_frame": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                    },
                ),
                "end_frame": (
                    "INT",
                    {
                        "default": 40,
                        "min": 20,
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    FUNCTION = "get_current_viewport"
    CATEGORY = "Omniverse"

    def get_current_viewport(self):

        headers = {"Content-Type": "application/json"}

        url = "http://localhost:8111"
        path = "/viewport-capture/simple-capture"

        response = requests.post(f"{url}{path}", headers=headers)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}. Error: {response.text}")
            return Image.new("RGB", (1920, 1080))

        response_image_path = response.json()["output_url_path"]
        image_url = f"{url}{response_image_path}"

        image = Image.open(requests.get(image_url, stream=True).raw)
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")


NODE_CLASS_MAPPINGS = {
    "OmniViewportFrameNode": OmniViewportFrameNode,
    "OmniViewportRecordingNode": OmniViewportRecordingNode,
    "OmniViewportDepthNode": OmniViewportDepthNode,
    "OmniViewportSemanticSegmentationNode": OmniViewportSemanticSegmentationNode,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "OmniViewportFrameNode": "Screen Capture Omniverse Viewport",
    "OmniViewportRecordingNode": "Screen Record Omniverse Viewport",
    "OmniViewportDepthNode": "Retrieve Omniverse Depth Mask",
    "OmniViewportSemanticSegmentationNode": "Retrieve Omniverse Semantic Segmentation Mask",
}
