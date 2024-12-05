import requests
import os
from PIL import Image
from io import BytesIO

class OmniViewportNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    FUNCTION = "get_current_viewport"
    CATEGORY = "Omniverse"

    def get_current_viewport(self):

        headers = {"Content-Type": "application/json"}

        data = {
            "usd_stage_path": "omniverse://nucleus.githubhero.com/Projects/Assets/coffee_table_1.usd",
        }

        url = "http://localhost:8111"
        path = "/viewport-capture/simple-capture"

        post_url_path = os.path.join(url, path)

        response = requests.post(post_url_path, headers=headers, json=data)

        if response.status_code != 200:
            print(f'Request failed with status code {response.status_code}. Error: {response.text}')
            return Image.new("RGB", (1920, 1080))

        response_image_path = response.json()["captured_image_path"]
        image_url = os.path.join(url, response_image_path)
        image = requests.get(image_url)
        return Image.open(BytesIO(image.content))


NODE_CLASS_MAPPINGS = {"OmniViewportNode": OmniViewportNode}
NODE_DISPLAY_NAME_MAPPINGS = {"OmniViewportNode": "Omniverse Viewport Capture"}
