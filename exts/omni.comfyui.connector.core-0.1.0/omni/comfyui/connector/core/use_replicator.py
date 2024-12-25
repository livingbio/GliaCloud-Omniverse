import omni.replicator.core as rep
from omni.replicator.core.scripts.annotators import Annotator
from omni.replicator.core.scripts.writers_default.tools import colorize_normals
from omni.kit.viewport.utility import get_active_viewport

import carb
import numpy as np
from typing import Literal
import matplotlib.pyplot as plt

from .models.viewport_models import ViewportRecordRequestModel, ViewportRecordResponseModel
from .ext_utils import get_extension_data_path, join_with_replace

def _set_renderer(renderer: str) -> None:
    if renderer == 'realtime':
        rep.settings.set_render_rtx_realtime(antialiasing="DLAA")
    elif renderer == 'pathtraced':
        rep.settings.set_render_pathtraced(samples_per_pixel=64)

def _configure_annotator(name: str, render_products: str | list) -> Annotator:
    anno = rep.AnnotatorRegistry.get_annotator(name)
    anno.attach(render_products)
    return anno

def _colorize_depth(depth_data):
    near = 0.01
    far = 100
    new_depth_data = np.clip(depth_data, near, far)
    new_depth_data = (np.log(new_depth_data) - np.log(near)) / (np.log(far) - np.log(near))
    new_depth_data = 1.0 - new_depth_data

    new_depth_data = np.stack((new_depth_data, new_depth_data, new_depth_data), axis=2)

    return new_depth_data


def _colorize_depth2(depth_data):
    near = 0.01
    far = 100
    gamma = 1 / 2.2
    new_depth_data = (depth_data - near) / (far - near)
    new_depth_data = np.clip(new_depth_data, near, far)
    new_depth_data = new_depth_data**gamma
    new_depth_data = 1.0 - new_depth_data

    new_depth_data = np.stack((new_depth_data, new_depth_data, new_depth_data), axis=2)

    return new_depth_data


def _colorize_depth3(depth_data):
    near = 0.01
    far = 100
    new_depth_data = np.clip(depth_data, near, far)
    new_depth_data = (np.log(new_depth_data) - np.log(near)) / (np.log(far) - np.log(near))
    new_depth_data = 1.0 - new_depth_data
    depth_colormap = plt.cm.plasma(new_depth_data)

    return depth_colormap[:, :, :3]


async def run(
    request: ViewportRecordRequestModel = ViewportRecordRequestModel()
) -> ViewportRecordResponseModel:

    response_model = ViewportRecordResponseModel()

    _viewport = get_active_viewport()
    if not _viewport or _viewport.frame_info.get("viewport_handle", None) is None:
        response_model.details_message = "Viewport is not properly loaded for rendering"
        return response_model

    active_camera_path = _viewport.camera_path
    render_products = rep.create.render_product(active_camera_path, (1920, 1080))

    _set_renderer(request.renderer)

    _ext_data_path = get_extension_data_path()

    rgb_annotator = _configure_annotator("rgb", render_products)
    normals_annotator = _configure_annotator("normals", render_products)
    depth_annotator = _configure_annotator("distance_to_camera", render_products)

    rgb_data_list = []
    normals_data_list = []
    depth_data_list = []

    for _ in range(request.num_frames_to_record):
        await rep.orchestrator.step_async()

        rgb_data: np.ndarray[tuple[int, int, Literal[4]], np.uint8] = rgb_annotator.get_data()

        rgb_data = rgb_data[:, :, :3]
        rgb_data = rgb_data / 255.0

        rgb_data_list.append(rgb_data)

        normals_data: np.ndarray[tuple[int, int, Literal[4]], np.float32] = normals_annotator.get_data()
        normals_data = colorize_normals(normals_data)
        normals_data = normals_data[:, :, :3]
        normals_data = normals_data / 255.0

        # normals_data_list.append(normals_data)

        depth_data: np.ndarray[tuple[int, int], np.float32] = depth_annotator.get_data()
        depth_data1 = _colorize_depth(depth_data)
        depth_data2 = _colorize_depth3(depth_data)

        depth_data_list.append(depth_data1)
        normals_data_list.append(depth_data2)

    rep.orchestrator.stop()

    rgb_data_stack = np.stack(rgb_data_list, axis=0)
    rgb_data_path = join_with_replace(_ext_data_path, "replicator/rgb.npy")
    np.save(rgb_data_path, arr=rgb_data_stack, allow_pickle=False)

    normals_data_stack = np.stack(normals_data_list, axis=0)
    normals_data_path = join_with_replace(_ext_data_path, "replicator/normals.npy")
    np.save(normals_data_path, arr=normals_data_stack, allow_pickle=False)

    depth_data_stack = np.stack(depth_data_list, axis=0)
    depth_data_path = join_with_replace(_ext_data_path, "replicator/depth.npy")
    np.save(depth_data_path, arr=depth_data_stack, allow_pickle=False)

    response_model.output_paths = {"rgb": rgb_data_path, "normals": normals_data_path, "depth": depth_data_path}
    response_model.success = True
    response_model.details_message = "Contains rgb, normals, and depth data."

    return response_model
