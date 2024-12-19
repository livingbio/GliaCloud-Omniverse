import requests
import numpy
import torch
from PIL import Image, ImageOps
from io import BytesIO


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
        image = numpy.array(image).astype(numpy.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")


class OmniViewportSequenceNode:

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
        image = numpy.array(image).astype(numpy.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
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
        image = numpy.array(image).astype(numpy.float32) / 255.0
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
        image = numpy.array(image).astype(numpy.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return (image,)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")


NODE_CLASS_MAPPINGS = {
    "OmniViewportFrameNode": OmniViewportFrameNode,
    "OmniViewportSequenceNode": OmniViewportSequenceNode,
    "OmniViewportDepthNode": OmniViewportDepthNode,
    "OmniViewportSemanticSegmentationNode": OmniViewportSemanticSegmentationNode,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "OmniViewportFrameNode": "Capture Omniverse Viewport Frame",
    "OmniViewportSequenceNode": "Capture Omniverse Viewport Sequence",
    "OmniViewportDepthNode": "Retrieve Omniverse Depth Mask",
    "OmniViewportSemanticSegmentationNode": "Retrieve Omniverse Semantic Segmentation Mask",
}
