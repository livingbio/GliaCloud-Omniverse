# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
__all__ = ["ComfyUIEditorExtension"]

import asyncio
from functools import partial
import omni.ext
import omni.kit.ui
from .editor_window import GraphWindow
from .node_registry_model import NodeRegistryQuickSearchModel
from omni.kit.graph.editor.core.graph_editor_core_tree_delegate import GraphEditorCoreTreeDelegate

_extension_instance = None


class ComfyUIEditorExtension(omni.ext.IExt):
    """Graph Editor Example"""
    WINDOW_NAME = GraphWindow.title
    MENU_PATH = "Window/GliaCloud Custom/" + WINDOW_NAME

    def on_startup(self):
        """create the graph window"""

        global _extension_instance
        _extension_instance = self

        self._window = None

        self._menu = None

        editor_menu = omni.kit.ui.get_editor_menu()
        if (editor_menu):
            self._menu = editor_menu.add_item(ComfyUIEditorExtension.MENU_PATH, self._on_menu_click, toggle=True, value=True)
        
        self.show_window(self._menu, True)

        # Quick Search subscription
        self._sub = None

        app = omni.kit.app.get_app_interface()
        ext_manager = app.get_extension_manager()
        self.__extensions_subscription = []

        self.__extensions_subscription.append(
            ext_manager.subscribe_to_extension_enable(
                partial(self._on_extensions_changed, True),
                partial(self._on_extensions_changed, False),
                ext_name="omni.kit.window.quicksearch",
                hook_name="omni.kit.graph.editor.example listener",
            )
        )

    def on_shutdown(self):
        global _extension_instance
        _extension_instance = None
        self.__extensions_subscription = None

        # deregister quick search model
        if self._sub is not None:
            del self._sub
            self._sub = None

        if self._window is not None:
            self._window.destroy()
            self._window = None

    def _is_window_focused(self) -> bool:
        """Returns True if the example Graph window exists and focused"""
        return self._window and self._window.focused

    def _on_menu_click(self, menu, toggled):
        self.show_window(menu, toggled)

    async def _destroy_window_async(self):
        # wait one frame, this is due to the one frame defer in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def show_window(self, menu, toggled):
        if toggled:
            if self._window is None:
                self._window = GraphWindow()
                self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
            else:
                self._window.show()
        else:
            asyncio.ensure_future(self._destroy_window_async())

    def _visiblity_changed_fn(self, visible):
        if self._menu:
            omni.kit.ui.get_editor_menu().set_value(ComfyUIEditorExtension.MENU_PATH, visible)
            self.show_window(None, visible)

    @staticmethod
    def add_node(mime_data: str):
        """Adds a node to the current example Graph window"""
        if not _extension_instance:
            return

        self = _extension_instance
        if not self._window:
            return

        class CustomEvent:
            def __init__(self, mime_data):
                self.mime_data = mime_data
                self.x = None
                self.y = None

        if self._window._main_widget:
            self._window._main_widget.on_drop(CustomEvent(mime_data))

    def _on_extensions_changed(self, loaded: bool, ext_id: str):
        """Called when the Quick Search extension is loaded/unloaded"""
        if loaded:
            from omni.kit.window.quicksearch import QuickSearchRegistry

            # Register simple model in Quick Search
            self._sub = QuickSearchRegistry().register_quick_search_model(
                "Graph editor nodes",
                NodeRegistryQuickSearchModel,
                GraphEditorCoreTreeDelegate,
                accept_fn=self._is_window_focused,
                priority=0
            )
        else:
            # Deregister simple model in Quick Search
            del self._sub
            self._sub = None
