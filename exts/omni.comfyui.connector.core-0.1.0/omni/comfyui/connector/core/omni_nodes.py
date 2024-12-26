import requests
import numpy as np
import torch  # type: ignore #
from PIL import Image, ImageOps


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
