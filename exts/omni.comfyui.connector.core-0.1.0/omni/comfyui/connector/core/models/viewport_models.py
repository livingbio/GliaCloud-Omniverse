from pydantic import BaseModel, Field, validator
from typing import Optional, Dict


class ViewportRecordRequestModel(BaseModel):
    """Model describing the request to record a viewport."""

    num_frames_to_record: int = Field(
        default=100,
        title="Capture Status",
        description="Status of the recording of the given USD stage.",
    )
    renderer: str = Field(
        default="realtime",
        title="Viewport Renderer",
        description="Renderer used to record viewport",
    )

    @validator("renderer", allow_reuse=True)
    @classmethod
    def validate_renderer(cls, renderer: str) -> str:
        RENDERER_OPTIONS = ["realtime", "pathtraced"]

        renderer = renderer.lower()
        if renderer not in RENDERER_OPTIONS:
            error_message = "Renderer input must be one of the following options in string format: "
            error_message += ", ".join(f"'{r}'" for r in RENDERER_OPTIONS)

            raise ValueError(error_message)

        return renderer


# We will also define a model to handle the delivery of responses back to clients.
#
# Just like the model used to handle incoming requests, the model to deliver responses will not only help define
# default values of response parameters, but also in documenting the values clients can expect using the OpenAPI
# specification format.
class ViewportRecordResponseModel(BaseModel):
    """Model describing the response to the request to record a viewport."""

    success: bool = Field(
        default=False,
        title="Capture s=Status",
        description="Status of the recording of the given USD stage.",
    )
    output_paths: Optional[Dict[str, str]] = Field(
        default=None,
        title="Output Data",
        description="A dictionary mapping annotators to the path where it wrote its data.",
    )
    details_message: str = Field(
        default="No details available.",
        title="Details Message",
        description="Message with details about the operation.",
    )
