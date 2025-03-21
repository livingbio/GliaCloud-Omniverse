import omni.replicator.core as rep
from omni.replicator.core.scripts.annotators import Annotator
from omni.replicator.core.scripts.writers_default.tools import colorize_segmentation
from omni.kit.viewport.utility import get_active_viewport
from semantics.schema.editor import get_prim_auto_label, add_prim_semantics, LabelWriteType
import omni.usd
from omni.usd import UsdContext
import omni.kit.actions.core

import numpy as np
from typing import Literal
import carb
from functools import partial

from .models.viewport_models import ViewportRecordRequestModel, ViewportRecordResponseModel
from .ext_utils import get_extension_data_path, join_with_replace

async def _add_auto_semantics():
    _output_str = ""

    _prim_types_filter = "Mesh, Material, Skeleton"
    _prefixes_to_remove = "SM, MI, Mat"
    _suffixes_to_remove = "Mat, 6M"

    prim_types = [prim_type for prim_type in _prim_types_filter.replace(" ", "").split(",") if prim_type]
    prefixes = [prefix for prefix in _prefixes_to_remove.replace(" ", "").split(",") if prefix]
    suffixes = [suffix for suffix in _suffixes_to_remove.replace(" ", "").split(",") if suffix]

    get_prim_data = partial(
        get_prim_auto_label,
        prim_types=prim_types,
        remove_numerical_ending=True,
        prefixes=prefixes,
        suffixes=suffixes,
        apply_cumulatively=True,
        remove_separators=True,
    )
    add_prim_data = partial(
        add_prim_semantics, type="class", write_type=LabelWriteType.NEW, preview=False
    )

    context: UsdContext = omni.usd.get_context()
    for prim in context.get_stage().Traverse():
        label = get_prim_data(prim)
        if label:
            _output_str += add_prim_data(prim, data=label)

    carb.log_warn(_output_str)
    return True

def _set_renderer(renderer: str) -> None:
    if renderer == "realtime":
        rep.settings.set_render_rtx_realtime(antialiasing="DLAA")
    elif renderer == "pathtraced":
        rep.settings.set_render_pathtraced(samples_per_pixel=64)

    carb.log_warn(f'Replicator renderer set to {renderer}.')

def _configure_annotator(name: str, render_products: str | list) -> Annotator:
    anno = rep.AnnotatorRegistry.get_annotator(name)
    anno.attach(render_products)
    return anno

async def run(request: ViewportRecordRequestModel = ViewportRecordRequestModel()) -> ViewportRecordResponseModel:

    response_model = ViewportRecordResponseModel()

    _viewport = get_active_viewport()
    if not _viewport or _viewport.frame_info.get("viewport_handle", None) is None:
        response_model.details_message = "Viewport is not properly loaded for rendering"
        return response_model

    save_result = await _add_auto_semantics()
    if not save_result:
        response_model.details_message = "Stage failed to save after adding semantics."
        return response_model

    active_camera_path = _viewport.camera_path
    render_products = rep.create.render_product(active_camera_path, (1920, 1080))

    _set_renderer(request.renderer)

    _ext_data_path = get_extension_data_path()

    rgb_annotator = _configure_annotator("rgb", render_products)
    normals_annotator = _configure_annotator("normals", render_products)
    depth_annotator = _configure_annotator("distance_to_camera", render_products)
    inst_id_seg_annotator = _configure_annotator("instance_id_segmentation_fast", render_products)
    semantic_seg_annotator = _configure_annotator("semantic_segmentation", render_products)

    replicator_data_path = join_with_replace(_ext_data_path, "replicator")

    rgb_identifier = "rgb_data/rgb_"
    normals_identifier = "normals_data/normals_"
    depth_identifier = "depth_data/depth_"
    inst_id_seg_identifier = "inst_id_seg_data/inst_id_seg_"
    semantic_seg_identifier = "semantic_seg_data/semantic_seg_"

    backend = rep.BackendDispatch({"paths": {"out_dir": replicator_data_path}})

    for frame in range(request.num_frames_to_record):
        await rep.orchestrator.step_async()

        rgb_data: np.ndarray[tuple[int, int, Literal[4]], np.uint8] = rgb_annotator.get_data()
        backend.write_array(rgb_identifier + str(frame) + ".npy", rgb_data)

        normals_data: np.ndarray[tuple[int, int, Literal[4]], np.float32] = normals_annotator.get_data()
        backend.write_array(normals_identifier + str(frame) + ".npy", normals_data)

        depth_data: np.ndarray[tuple[int, int], np.float32] = depth_annotator.get_data()
        backend.write_array(depth_identifier + str(frame) + ".npy", depth_data)

        inst_id_seg_dict: np.ndarray[tuple[int, int], np.uint8] = inst_id_seg_annotator.get_data()
        inst_id_seg_data, _palette, _mapping = colorize_segmentation(
            data=inst_id_seg_dict["data"],
            labels=inst_id_seg_dict["info"]["idToLabels"]
        )

        backend.write_array(inst_id_seg_identifier + str(frame) + ".npy", inst_id_seg_data)

        semantic_seg_dict: np.ndarray[tuple[int, int], np.uint8] = semantic_seg_annotator.get_data()
        semantic_seg_data, _palette, _mapping = colorize_segmentation(
            data=semantic_seg_dict["data"], labels=semantic_seg_dict["info"]["idToLabels"]
        )

        backend.write_array(semantic_seg_identifier + str(frame) + ".npy", semantic_seg_data)

        backend.wait_until_done()

    rep.orchestrator.stop()

    response_model.output_paths = {
        "rgb": join_with_replace(replicator_data_path, rgb_identifier),
        "normals": join_with_replace(replicator_data_path, normals_identifier),
        "depth": join_with_replace(replicator_data_path, depth_identifier),
        "inst_id_seg": join_with_replace(replicator_data_path, inst_id_seg_identifier),
        "semantic_seg": join_with_replace(replicator_data_path, semantic_seg_identifier),
    }

    response_model.success = True
    response_model.details_message = "Contains rgb, normals, depth, instance-id-segmented, & semantic-segmented data."

    return response_model
