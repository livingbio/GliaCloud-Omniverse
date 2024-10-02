# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.kit.test
import pathlib
import carb
import omni.usd
import omni.kit.app
from omni.kit.test import AsyncTestCase
from omni.kit.window.reshade_editor.reshade_window import ReshadeWindow

EXTENSION_FOLDER_PATH = pathlib.Path(omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__))
TESTS_PATH = EXTENSION_FOLDER_PATH.joinpath("data/tests")

class TestReshadeEditor(AsyncTestCase):
    async def setUp(self):
        super().setUp()
        await omni.usd.get_context().new_stage_async()
        settings = carb.settings.get_settings()
        settings.set("/rtx/reshade/enable", "true")
        settings.set("/rtx/reshade/presetFilePath", f"{TESTS_PATH}/preset.ini")
        settings.set("/rtx/reshade/effectSearchDirPath", f"{TESTS_PATH}")
        # Update app a few times for effects to load and compile
        for i in range(20):
            await omni.kit.app.get_app().next_update_async()

    async def test_variable_list(self):
        w = ReshadeWindow(None)
        self.assertIsNotNone(w._window)

        effects = w._vmodel.get_item_children(None)
        self.assertIsNotNone(effects)
        self.assertTrue(len(effects) == 1)  # data/tests/simple.fx

        variables = w._vmodel.get_item_children(effects[0])
        self.assertIsNotNone(effects)
        self.assertTrue(len(variables) == 1)  # "fill_color" in data/tests/simple.fx

    async def test_technique_list(self):
        w = ReshadeWindow(None)
        self.assertIsNotNone(w._window)

        techniques = w._tmodel.get_item_children(None)
        self.assertIsNotNone(techniques)
        self.assertTrue(len(techniques) == 1)  # technique "simple" in data/tests/simple.fx
