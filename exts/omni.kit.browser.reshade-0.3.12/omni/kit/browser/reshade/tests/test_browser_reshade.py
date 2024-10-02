## Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
##
## NVIDIA CORPORATION and its licensors retain all intellectual property
## and proprietary rights in and to this software, related documentation
## and any modifications thereto.  Any use, reproduction, disclosure or
## distribution of this software and related documentation without an express
## license agreement from NVIDIA CORPORATION is strictly prohibited.
##
import omni.kit.app
import omni.kit.test
import omni.ui as ui
from omni.ui.tests.test_base import OmniUiTest

import asyncio
from pathlib import Path

CURRENT_PATH = Path(__file__).parent
TEST_DATA_PATH = CURRENT_PATH.parent.parent.parent.parent.parent.joinpath("data").joinpath("tests")


class TestReshadeBrowser(OmniUiTest):
    # Before running each test
    async def setUp(self):
        await super().setUp()

        self._golden_img_dir = TEST_DATA_PATH.absolute().joinpath("golden_img").absolute()

    # After running each test
    async def tearDown(self):
        await super().tearDown()

    async def test_browser_ui(self):
        browser = omni.kit.browser.reshade.get_instance()
        await self.docked_test_window(window=browser._window, width=1280, height=720)
        # Wait for folder and thumbnails load completed
        await asyncio.sleep(8)

        await self.finalize_test(golden_img_dir=self._golden_img_dir, golden_img_name="test_reshade_browser.png")
