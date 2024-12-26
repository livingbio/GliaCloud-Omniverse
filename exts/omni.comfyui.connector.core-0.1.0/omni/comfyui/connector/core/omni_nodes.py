import requests
import numpy as np
import torch  # type: ignore #
from PIL import Image, ImageOps
from comfy.utils import ProgressBar
from typing import Literal
from threading import Thread
from time import perf_counter


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

def _colorize_rgb(data: list):
    start = round(perf_counter(), 2)

    rgb_data = data[0]

    rgb_data = rgb_data / 255.0
    rgb_data = torch.from_numpy(rgb_data)

    data[0] = rgb_data

    end = round(perf_counter(), 2)
    print(f"RGB colorization took {end - start}, starting at {start} and ending at {end}")

def _colorize_normals(data: list):
    start = round(perf_counter(), 2)

    normals_data = data[0]

    normals_data = ((normals_data * 0.5 + 0.5) * 255).astype(np.uint8)
    normals_data = normals_data / 255.0
    normals_data = torch.from_numpy(normals_data)

    data[0] = normals_data

    end = round(perf_counter(), 2)
    print(f"Normals colorization took {end - start}, starting at {start} and ending at {end}")

def _colorize_depth(data: list):
    start = round(perf_counter(), 2)

    depth_data = data[0]

    near = 0.01
    far = 100
    depth_data = np.clip(depth_data, near, far)
    depth_data = (np.log(depth_data) - np.log(near)) / (np.log(far) - np.log(near))
    depth_data = 1.0 - depth_data

    alpha_data = np.full((depth_data.shape[0], depth_data.shape[1]), 1)

    depth_data = np.stack((depth_data, depth_data, depth_data, alpha_data), axis=2)
    depth_data = torch.from_numpy(depth_data)

    data[0] = depth_data

    end = round(perf_counter(), 2)

    print(f'Depth colorization took {end - start}, starting at {start} and ending at {end}')


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

        H, W, C = 1080, 1920, 4

        pbar = ProgressBar(num_frames_to_record)

        rgb_tensor = torch.zeros((num_frames_to_record, H, W, C))
        normals_tensor = torch.zeros((num_frames_to_record, H, W, C))
        depth_tensor = torch.zeros((num_frames_to_record, H, W, C))

        for frame in range(num_frames_to_record):
            rgb_frame_path = response.json()["output_paths"]["rgb"] + str(frame) + ".npy"
            normals_frame_path = str(response.json()["output_paths"]["normals"]) + str(frame) + ".npy"
            depth_frame_path = str(response.json()["output_paths"]["depth"]) + str(frame) + ".npy"

            rgb_frame = [np.load(rgb_frame_path)]
            normals_frame = [np.load(normals_frame_path)]
            depth_frame = [np.load(depth_frame_path)]

            rgb_thread = Thread(target=_colorize_rgb, args=[rgb_frame])
            normals_thread = Thread(target=_colorize_normals, args=[normals_frame])
            depth_thread = Thread(target=_colorize_depth, args=[depth_frame])

            rgb_thread.start()
            normals_thread.start()
            depth_thread.start()

            rgb_thread.join()
            normals_thread.join()
            depth_thread.join()

            rgb_tensor[frame] = rgb_frame[0]
            normals_tensor[frame] = normals_frame[0]
            depth_tensor[frame] = depth_frame[0]

            pbar.update_absolute(frame, num_frames_to_record)

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
