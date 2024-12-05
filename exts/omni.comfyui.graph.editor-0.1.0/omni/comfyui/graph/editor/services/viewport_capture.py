from typing import Optional

from pydantic import BaseModel, Field

import carb

from omni.services.core import routers

from ..ext_utils import capture_viewport


router = routers.ServiceAPIRouter()


# Let's define a model to handle the parsing of incoming requests.
#
# Using `pydantic` to handle data-parsing duties makes it less cumbersome for us to do express types, default values,
# minimum/maximum values, etc. while also taking care of documenting input and output properties of our service using
# the OpenAPI specification format.
class ViewportCaptureRequestModel(BaseModel):
    """Model describing the request to capture a viewport as an image."""

    # HACK - sample path: omniverse://nucleus.githubhero.com/Projects/Assets/coffee_table_1.usd
    usd_stage_path: str = Field(
        ...,
        title="Path of the USD stage for which to capture an image",
        description="Location where the USD stage to capture can be found.",
    )
    # If required, add additional capture response options in subsequent iterations.
    # [...]


# We will also define a model to handle the delivery of responses back to clients.
#
# Just like the model used to handle incoming requests, the model to deliver responses will not only help define
# default values of response parameters, but also in documenting the values clients can expect using the OpenAPI
# specification format.
class ViewportCaptureResponseModel(BaseModel):
    """Model describing the response to the request to capture a viewport as an image."""

    success: bool = Field(
        default=False,
        title="Capture status",
        description="Status of the capture of the given USD stage.",
    )
    output_url_path: Optional[str] = Field(
        default=None,
        title="Output URL Path",
        description="The URL path where the captured image will be served from",
    )
    error_message: Optional[str] = Field(
        default=None,
        title="Error message",
        description="Optional error message in case the operation was not successful.",
    )


# Using the `@router` annotation, we'll tag our `capture` function handler to document the responses and path of the
# API, once again using the OpenAPI specification format.
@router.post(
    path="/simple-capture",
    summary="Capture a given USD stage",
    description="Capture a given USD stage as an image.",
    response_model=ViewportCaptureResponseModel,
    tags=["Viewport Capture"],
)
async def simple_capture(
    request: ViewportCaptureRequestModel,
) -> ViewportCaptureResponseModel:
    # For now, let's just print incoming request to the log to confirm all components of our extension are properly
    # wired together:
    carb.log_warn(f'Received a request to capture an image of "{request.usd_stage_path}".')
    success, output_url_path, error_message = await capture_viewport(usd_stage_path=request.usd_stage_path)

    return ViewportCaptureResponseModel(
        success=success,
        output_url_path=output_url_path,
        error_message=error_message,
    )
