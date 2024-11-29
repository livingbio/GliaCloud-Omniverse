class OmniViewportNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    FUNCTION = "get_current_viewport"
    CATEGORY = "Omniverse"

    def get_current_viewport(self):
        pass
