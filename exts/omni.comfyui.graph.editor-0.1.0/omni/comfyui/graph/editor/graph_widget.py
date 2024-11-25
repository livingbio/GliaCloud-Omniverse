# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
__all__ = ["GraphWidget"]

import asyncio
import json
import omni.kit.app
import omni.ui as ui
from omni.kit.graph.editor.core import GraphEditorCoreWidget
from omni.kit.widget.graph import GraphModel, GraphView
from omni.ui import color as cl
from pathlib import Path
import carb
import os
import platform
from enum import IntEnum
from functools import partial

from .simple_model import SimpleGraphModel
from .node_registry_model import NodeRegistryModel

CURRENT_PATH = Path(__file__).parent
EXT_PATH = CURRENT_PATH.parent.parent.parent.parent.parent
ICON_PATH = EXT_PATH.joinpath("icons")
INPUT_PATH = EXT_PATH.joinpath("graphs")

BACKGROUND = cl("#1F2123")

# Setup the Class you want to Design HERE
from omni.kit.graph.delegate.neo.delegate import NeoGraphNodeDelegate
from omni.kit.graph.delegate.default.delegate import GraphNodeDelegate as DefaultNodeDelegate
from omni.kit.graph.delegate.default.backdrop_delegate import BackdropDelegate as DefaultBackdropDelegate
from omni.kit.graph.delegate.modern.note_delegate import NoteDelegate as ModernNoteDelegate
from omni.kit.graph.delegate.default.compound_node_delegate import CompoundInputOutputNodeDelegate as DefaultCompoundInputOutputNodeDelegate
from omni.kit.graph.delegate.default.compound_node_delegate import CompoundNodeDelegate as DefaultCompoundNodeDelegate

from omni.kit.graph.delegate.modern.delegate import GraphNodeDelegate as ModernNodeDelegate
from .nodes import GraphNode


class DelegateNameItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)


class DelegateNameModel(ui.AbstractItemModel):
    def __init__(self, names):
        super().__init__()

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(lambda a: self._item_changed(None))

        self._items = [
            DelegateNameItem(text)
            for text in names
        ]

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model


class GraphViewConnectionsOnTop(GraphView):
    def __init__(self, **kwargs):
        kwargs["connections_on_top"] = True
        kwargs["zoom_min"] = 0.3
        kwargs["zoom_max"] = 3
        super().__init__(**kwargs)


class GraphWidget(GraphEditorCoreWidget):
    """graph widget which is inherited from GraphEditorCoreWidget"""
    class DelegateType(IntEnum):
        Neo = 0
        Default = 1
        Modern = 2

    @staticmethod
    def __get_workspace_dir() -> str:
        """Return the workspace file"""
        extension_path = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        filepicker_path = f"{extension_path}/graphs/"
        if platform.system().lower() == "windows":
            filepicker_path = filepicker_path.replace("/", "\\")

        return filepicker_path

    def __init__(self, **kwargs):
        self._graph_root = None
        # define the graph model to be None until we get the data
        self._graph_model = None
        # initialize the graph delegate

        delegate_type = kwargs.pop("delegate_type", int(self.DelegateType.Modern))
        self._delegate_name_model = DelegateNameModel(self.DelegateType.__members__.keys())
        self._delegate_name_model.get_item_value_model(None, 0).as_int = delegate_type
        self._delegate_style = {}
        self._update_delegate(delegate_type)

        # catalog model for the left side tree view
        self._registry_model = NodeRegistryModel()
        self.__context_menu = None
        self.__open_file_dialog = None
        self.__save_file_dialog = None
        self.__pop_up_dialog = None
        self.__create_dialog = None

        toolbar_items = [
            { "name": "open", "icon": f"{ICON_PATH}/open.svg", "on_clicked": self.open_graph},
            { "name": "save", "icon": f"{ICON_PATH}/save.svg", "on_clicked": self.save_graph},
            { "name": "new", "icon": f"{ICON_PATH}/new.svg", "on_clicked": self.clear_graph},
            ]

        super().__init__(
            delegate=self._graph_delegate,
            style=self._delegate_style,
            catalog_model=self._registry_model,
            toolbar_items=toolbar_items,
            view_type=GraphViewConnectionsOnTop,
            **kwargs,
        )

    def _on_delegate_changed(self, model, item):
        """function called when delegate is changed"""
        delegate_type = model.get_item_value_model(item, 0).as_int
        self._update_delegate(delegate_type)

        self.style = self._delegate_style
        self._graph_view.set_delegate(self._graph_delegate)

    def _update_delegate(self, delegate_type):
        # Update the style
        # because the delegate will update in a couple of frames, so we still need the old style.
        if delegate_type == int(self.DelegateType.Neo):
            self._graph_delegate = NeoGraphNodeDelegate()
            self._delegate_style.update(self.get_specialized_style(0xFFFFFFFF))
        elif delegate_type == int(self.DelegateType.Default):
            self._graph_delegate = DefaultNodeDelegate()
            self._graph_delegate.add_route(DefaultBackdropDelegate(), type="Backdrop")
            self._graph_delegate.add_route(DefaultCompoundNodeDelegate(), type="Compound")
            self._graph_delegate.add_route(DefaultCompoundInputOutputNodeDelegate(), type="InputNode")
            self._graph_delegate.add_route(DefaultCompoundInputOutputNodeDelegate(), type="OutputNode")
            self._delegate_style.update(self.get_specialized_style(0xFFFFFFFF))
        elif delegate_type == int(self.DelegateType.Modern):
            self._graph_delegate = ModernNodeDelegate()
            self._graph_delegate.add_route(ModernNoteDelegate(), type="OmniNote")
            self._delegate_style.update(self.get_specialized_style())

    def clear_graph(self):
        self.model=None

    def on_build_graph(self):
        super().on_build_graph()
        with ui.Frame(height=0):
            with ui.HStack():
                ui.Spacer()
                with ui.VStack(content_clipping=1, width=70):
                    ui.Spacer(height=10)
                    with ui.HStack(width=0):
                        ui.Label("Change Delegate", name="Change Delegate", width=10)
                        ui.Spacer(width = 10)
                        self._delegate_name = ui.ComboBox(self._delegate_name_model, width=200, style={"background_color": 0xFF333333})
                        self._delegate_name.model.add_item_changed_fn(self._on_delegate_changed)
                        ui.Spacer(width = 15)

    def on_build_breadcrumbs(self):
        # add space padding around the navigation
        with ui.VStack():
            ui.Spacer(height=10)
            with ui.HStack(width=0):
                ui.Spacer(width=15)
                super().on_build_breadcrumbs()

    def _on_filter_item(self, item) -> bool:
        """Callback to filter the choices of file names in the open or save dialog"""
        # Show only files with listed extensions
        return os.path.splitext(item.path)[1] == ".json"

    def _on_error(self, error: str):
        """Callback executed when there is an error in the file dialogs"""
        carb.log_error(error)

    def open_graph(self):
        def _on_click_open(file_name: str, directory_path: str):
            """Callback executed when the user selects a file in the open file dialog
            """
            fullpath = os.path.join(directory_path, file_name)
            self.read_graph(fullpath)
            if self.__open_file_dialog:
                self.__open_file_dialog.hide()

        if self.__open_file_dialog:
            self.__open_file_dialog.destroy()

        from omni.kit.window.filepicker import FilePickerDialog
        self.__open_file_dialog = FilePickerDialog(
                "Open graph .json File",
                apply_button_label="Open",
                click_apply_handler=lambda f, d: _on_click_open(f, d),
                item_filter_options=["*.json", ".json Files (*.json)", "All Files (*)"],
                item_filter_fn=lambda item: self._on_filter_item(item),
                current_directory=self.__get_workspace_dir()
            )
        self.__open_file_dialog.show()

    def save_graph(self):
        def _on_click_save(file_name: str, directory_path: str):
            """Callback executed when the user selects a file in the save file dialog
            """
            fullpath = os.path.join(directory_path, file_name)

            def __save_as_json(dialog):
                if self.__pop_up_dialog:
                    self.__pop_up_dialog.hide()
                self._graph_model.write_graph(fullpath)

            def __rename_json(dialog):
                if self.__pop_up_dialog:
                    self.__pop_up_dialog.hide()
                self.__save_file_dialog.show()

            if os.path.exists(fullpath):
                from omni.kit.window.popup_dialog import OptionsDialog
                self.__pop_up_dialog = OptionsDialog(
                    title="Overwrite graph .json file",
                    message=f"File {os.path.basename(fullpath)} already exists, do you want to overwrite it?",
                    ok_label="Yes",
                    cancel_label="No",
                    ok_handler=__save_as_json,
                    cancel_handler=__rename_json)
                self.__pop_up_dialog.show()
            else:
                __save_as_json(fullpath)

            self.__save_file_dialog.hide()

        if self.__open_file_dialog:
            self.__open_file_dialog.destroy()

        from omni.kit.window.filepicker import FilePickerDialog
        self.__save_file_dialog = FilePickerDialog(
                "Save graph .json File",
                apply_button_label="Save",
                click_apply_handler=lambda f, d: _on_click_save(f, d),
                item_filter_options=["*.json", ".json Files (*.json)"],
                item_filter_fn=lambda item: self._on_filter_item(item),
                current_directory=self.__get_workspace_dir(),
            )
        self.__save_file_dialog.show()

    def destroy(self):
        self.__context_menu = None
        if self.__open_file_dialog:
            self.__open_file_dialog.destroy()
        self.__open_file_dialog = None
        if self.__save_file_dialog:
            self.__save_file_dialog.destroy()
        self.__save_file_dialog = None
        if self.__pop_up_dialog:
            self.__pop_up_dialog.destroy()
        self.__pop_up_dialog = None
        if self.__create_dialog:
            self.__create_dialog.destroy()
        self.__create_dialog = None

        self._registry_model.destroy()
        self._registry_model = None

        self._graph_delegate.destroy()
        self._graph_delegate = None

        if self._graph_model:
            self._graph_model.destroy()
        self._graph_model = None

        self._graph_root = None

        self._delegate_name_model = None

        super().destroy()

    def read_graph(self, file_path):
        with open(file_path) as json_file:
            json_data = json.loads(json_file.read())
            for graph in json_data:
                graph_data = json_data[graph]
                # we suppose all the nodes always belong to a graph
                # simply the problem a bit, we only care about the first graph we get
                if graph_data.get("type", "Node") == "Graph":
                    self._graph_root = GraphNode(graph)
                    self._graph_model = SimpleGraphModel(self._graph_root, graph_data)
                    self.model = self._graph_model
                    break
        if self._graph_root and self._graph_model:
            self.set_current_compound(self._graph_root)

    def create_graph(self):
        def __create_new_graph(dialog):
            if self.__create_dialog:
                self.__create_dialog.hide()
            graph_name = dialog.get_value()
            self._graph_root = GraphNode(graph_name)
            self._graph_model = SimpleGraphModel(self._graph_root)
            self.model = self._graph_model
            self.set_current_compound(self._graph_root)

        def __cancel(dialog):
            self.__create_dialog.hide()

        from omni.kit.window.popup_dialog import InputDialog
        self.__create_dialog = InputDialog(
            title=f"Create a new Graph",
            message="Enter graph name",
            default_value="MyGraph",
            ok_handler=__create_new_graph,
            cancel_handler=__cancel
        )
        self.__create_dialog.show()

    def on_build_startup(self):
        """ this is an override for the function in base Class while building the graph
            we define the graph model with serializing a json file
        """
        with ui.ZStack():
            ICON_SIZE = 120
            # Background
            ui.Rectangle(style_type_name_override="Graph")
            # Two buttons
            with ui.VStack(content_clipping=True):
                ui.Spacer()
                with ui.HStack(height=0):
                    ICON_SIZE = 120
                    ui.Spacer()
                    ui.Button(
                        "Open Graph",
                        name="Open Graph",
                        width=0,
                        image_width=ICON_SIZE,
                        image_height=ICON_SIZE,
                        image_url=f"{ICON_PATH}/type_scene_graph_dark.svg",
                        spacing=5,
                        clicked_fn=self.open_graph,
                    )
                    # 20 because the button's padding is 10
                    ui.Label("    OR    ", name="OR", width=0, height=ICON_SIZE + 20)
                    ui.Button(
                        "Create Graph",
                        name="Create Graph",
                        width=0,
                        image_width=ICON_SIZE,
                        image_height=ICON_SIZE,
                        image_url=f"{ICON_PATH}/type_scene_graph_dark.svg",
                        spacing=5,
                        clicked_fn=self.create_graph,
                    )
                    ui.Spacer()
                ui.Spacer()

    def get_specialized_style(self, color=None):
        # It's optional. It's here in case we have colors different from colors
        # of omni.kit.graph.editor.core.
        style = self._graph_delegate.get_style(background=BACKGROUND)

        # node types
        style.update(
            self._graph_delegate.specialized_color_style("Rendering", 0xFF921F68, f"{ICON_PATH}/type_rendering_noBorder_dark.svg", color or 0xFF5A2045))
        style.update(
            self._graph_delegate.specialized_color_style("Material", 0xFFB97E9C, f"{ICON_PATH}/type_material_noBorder_dark.svg", color or 0xFF6E505F))
        style.update(
            self._graph_delegate.specialized_color_style("Texture", 0xFFC2665C, f"{ICON_PATH}/type_texture_noBorder_dark.svg", color or 0xFF72443F))
        style.update(
            self._graph_delegate.specialized_color_style("Function", 0xFFADFB47, f"{ICON_PATH}/type_function_noBorder_dark.svg", color or 0xFF688E33))
        style.update(
            self._graph_delegate.specialized_color_style("Math", 0xFF538A4A, f"{ICON_PATH}/type_math_noBorder_dark.svg", color or 0xFF3A5636))
        style.update(
            self._graph_delegate.specialized_color_style("Geometry", 0xFF576B53, f"{ICON_PATH}/type_geometry_noBorder_dark.svg", color or 0xFF3C463A))
        style.update(
            self._graph_delegate.specialized_color_style("Time", 0xFFDBA656, f"{ICON_PATH}/type_time_noBorder_dark.svg", color or 0xFF7F643C))
        style.update(
            self._graph_delegate.specialized_color_style("Animation", 0xFFDBA656, f"{ICON_PATH}/type_animation_noBorder_dark.svg", color or 0xFF7F643C))
        style.update(
            self._graph_delegate.specialized_color_style("Compound", 0xFF7C7457, f"{ICON_PATH}/type_scene_graph_noBorder_dark.svg", color or 0xFF4F4B3C))
        style.update(
            self._graph_delegate.specialized_color_style("InputNode", 0xFFCE5FE5, f"{ICON_PATH}/type_input_noBorder_dark.svg", color or 0xFF784084))
        style.update(
            self._graph_delegate.specialized_color_style("OutputNode", 0xFFCE5FE5, f"{ICON_PATH}/type_input_noBorder_dark.svg", color or 0xFF784084))
        style.update(
            self._graph_delegate.specialized_color_style("Debug", 0xFF6C569F, f"{ICON_PATH}/type_debug_noBorder_dark.svg", color or 0xFF473C60))
        style.update(
            self._graph_delegate.specialized_color_style("UI", 0xFF588A9E, f"{ICON_PATH}/type_ui_noBorder_dark.svg", color or 0xFF3D5660))
        style.update(
            self._graph_delegate.specialized_color_style("IO", 0xFF4D87EE, f"{ICON_PATH}/type_io_noBorder_dark.svg", color or 0xFF375588))
        style.update(
            self._graph_delegate.specialized_color_style("Backdrop", 0xFF9B9B9B, f"{ICON_PATH}/type_generic_noBorder_dark.svg", color or 0xFF5F5F5F))
        style.update(
            self._graph_delegate.specialized_color_style("Note", 0xFF8B9B9B, f"{ICON_PATH}/type_generic_noBorder_dark.svg", color or 0xFF5F5F5F))
        style.update(
            self._graph_delegate.specialized_color_style("Event", 0xFF7ABF20, f"{ICON_PATH}/type_event_noBorder_dark.svg", color or 0xFF4B6E1E))

        style.update(self._graph_delegate.specialized_port_style("bool", 0xFF1C1CE2))
        style.update(self._graph_delegate.specialized_port_style("str", 0xFF781FA5))
        style.update(self._graph_delegate.specialized_port_style("float", 0xFF88CF2A))
        style.update(self._graph_delegate.specialized_port_style("mesh", 0xFFD8B74B))
        style.update(self._graph_delegate.specialized_port_style("texture", 0xFFFF38B6))
        style.update(self._graph_delegate.specialized_port_style("color", 0xFFAD1122))
        style.update(self._graph_delegate.specialized_port_style("asset", 0xFF3C3ACC))
        style.update(self._graph_delegate.specialized_port_style("int", 0xFF5F5FE5))
        style.update(self._graph_delegate.specialized_port_style("material", 0xFF005FE5))
        style.update(self._graph_delegate.specialized_port_style("group", 0xFF1C1CE2))

        return style

    def on_right_mouse_button_pressed(self, items):
        """ this is an override for the function in base Class while right mouse button is pressed
            we create a context menu when right mouse button pressed
        """
        self.__context_menu = ui.Menu("Context menu")
        with self.__context_menu:
            ui.MenuItem("Delete Selection", triggered_fn=lambda: self._graph_model.delete_selection())
            ui.Separator()
            ui.MenuItem("Open All", triggered_fn=lambda: self._graph_view.set_expansion(GraphModel.ExpansionState.OPEN))
            ui.MenuItem(
                "Minimize All", triggered_fn=lambda: self._graph_view.set_expansion(GraphModel.ExpansionState.MINIMIZED)
            )
            ui.MenuItem(
                "Close All", triggered_fn=lambda: self._graph_view.set_expansion(GraphModel.ExpansionState.CLOSED)
            )
            ui.Separator()
            ui.MenuItem("Layout All", triggered_fn=lambda: self._graph_view.layout_all())
            ui.MenuItem("Focus on All", triggered_fn=lambda: self._graph_view.focus_on_nodes())
            ui.MenuItem("Focus on Selection", triggered_fn=lambda: self._graph_view.focus_on_nodes(self._graph_model.selection))

        self.__context_menu.show()

    def set_current_compound(self, item, focus=True):
        """This is called when the current graph is changed. Except the call in the current file, it is also called in
        `on_build_breadcrumbs`'s selected_fn
        """
        super().set_current_compound(item, focus)
        self._graph_model.current_graph = item

    def on_left_mouse_button_double_clicked(self, items):
        """ this is an override for the function in base Class while left mouse button is double clicked
            we enter into a subgraph when we double click a CompoundNode
        """
        # double click on a compound node will open the subgraph
        if not items:
            return

        # Open compound
        self.set_current_compound(items[0])

    def on_key_pressed(self, key, mod, pressed):
        """Called when the user presses a key"""
        self._graph_model.current_graph = self.get_current_graph_item()
        # clear the selection when press escape
        if key == int(carb.input.KeyboardInput.ESCAPE):
            self._graph_model.selection = []
            self._graph_model._item_changed(None)

        # when we hold D and move a node, all the input nodes of the selected node will moved together
        if key == int(carb.input.KeyboardInput.D):
            self._graph_model.move_descendant = pressed
            return

        # when we hold left_shift, we enter the multi-selection mode
        if key == int(carb.input.KeyboardInput.LEFT_SHIFT):
            self._graph_model.append_selection_mode = pressed
            return

        if not pressed or (mod & ui.Widget.FLAG_WANT_CAPTURE_KEYBOARD):
            return

        # when we press F, focus on the slected node. If there is no node selected, we will focus on the whole graph
        if key == int(carb.input.KeyboardInput.F) and mod == 0:
            self._graph_view.focus_on_nodes(self._graph_model.selection)

    def on_drop(self, event: ui.WidgetMouseDropEvent):
        """Called to create a node that was dropped to the window"""
        if event.x is None and event.y is None:
            # put the node at the Middle of the canvas
            event.x = self._graph_view.screen_position_x + self._graph_view.computed_width / 2
            event.y = self._graph_view.screen_position_y + self._graph_view.computed_height / 2

        position = self._graph_view.screen_to_canvas(event.x, event.y)
        data = event.mime_data
        self._graph_model.current_graph = self.get_current_graph_item()
        try:
            json_data = json.loads(data) or {}
            node_type_name = json_data.get("node_type", "Node")
            if node_type_name == "Input":
                self._isolation_model.add_input_or_output(position, 1)
            elif node_type_name == "Output":
                self._isolation_model.add_input_or_output(position, 0)
            else:
                self._graph_model.create_node(node_type_name, position)
        except json.decoder.JSONDecodeError:
            return

    def on_accept_drop(self, drop_data: str):
        """Called to check if drop_data has the acceptable node description"""
        return True