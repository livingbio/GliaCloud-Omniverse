from enum import Enum
import omni.ui as ui
import json

from pathlib import Path
CURRENT_PATH = Path(__file__).parent
EXT_PATH = CURRENT_PATH.parent.parent.parent.parent.parent
ICON_PATH = EXT_PATH.joinpath("icons")


class NodeBaseItem(ui.AbstractItem):
    """Node Base item for NodeRegistryModel"""

    def __init__(self, item_name: str, item_info: str, item_icon: str, item_type: str):
        super().__init__()
        # it has four value models, each of which defines one type of the information of the node
        self.name_model = ui.SimpleStringModel(item_name)
        self.info_model = ui.SimpleStringModel(item_info)
        self.icon_model = ui.SimpleStringModel(item_icon)
        self.type_model = ui.SimpleStringModel(item_type)

        # True when the item is visible, used for filtering nodes we want
        self.filtered = True

    # filter function, we filter out the nodes whose name_model or info_model contains the input text str
    def filter(self, text: str):
        if not text or text in self.name_model.as_string.lower() or text in self.info_model.as_string.lower():
            self.filtered = True
        else:
            self.filtered = False


class GroupItem(NodeBaseItem):
    """Group item for NodeRegistryModel """
    def __init__(self, group_name):
        super().__init__(group_name, "", "", "")
        self.filtered = True
        self.children = []

    # the group visibility filtering function, so there is any one of the node is visible, the group node item should
    # be visible
    def prefilter(self, text: str):
        group_visible = False
        for c in self.children:
            c.filter(text)
            group_visible |= c.filtered
        self.filtered = group_visible


class NodeRegistryModel(ui.AbstractItemModel):

    class Column(Enum):
        NAME = 0
        INFO = 1
        ICON = 2
        TYPE = 3

    def __init__(self, *args):
        super().__init__()
        # define two groups
        general_item = GroupItem("General")
        miscellaneous_item = GroupItem("Miscellaneous")
        self._children = [general_item, miscellaneous_item]
        # define groups' children
        general_item.children = [
            NodeBaseItem("Animation", "This is an animation node", f"{ICON_PATH}/type_animation_dark.svg", "Animation"),
            NodeBaseItem("Debug", "This is a debug node", f"{ICON_PATH}/type_debug_dark.svg", "Debug"),
            NodeBaseItem("Event", "This is an event node", f"{ICON_PATH}/type_event_dark.svg", "Event"),
            NodeBaseItem("Function", "This is a function node", f"{ICON_PATH}/type_function_dark.svg", "Function"),
            NodeBaseItem("Geometry", "This is a geometry node", f"{ICON_PATH}/type_geometry_dark.svg", "Geometry"),
            NodeBaseItem("IO", "This is an io node", f"{ICON_PATH}/type_io_dark.svg", "IO"),
            NodeBaseItem("Material", "This is a material node", f"{ICON_PATH}/type_material_dark.svg", "Material"),
            NodeBaseItem("Math", "This is a math node", f"{ICON_PATH}/type_math_dark.svg", "Math"),
            NodeBaseItem("Rendering", "This is a rendering node", f"{ICON_PATH}/type_rendering_dark.svg", "Rendering"),
            NodeBaseItem("Texture", "This is a texture node", f"{ICON_PATH}/type_texture_dark.svg", "Texture"),
            NodeBaseItem("Time", "This is a time node", f"{ICON_PATH}/type_time_dark.svg", "Time"),
            NodeBaseItem("UI", "This is a ui node", f"{ICON_PATH}/type_ui_dark.svg", "UI"),
        ]
        miscellaneous_item.children = [
            NodeBaseItem("Backdrop", "Create Backdrop for your Graph", f"{ICON_PATH}/type_generic_dark.svg", "Backdrop"),
            NodeBaseItem("OmniNote", "Create a Note for your Graph", f"{ICON_PATH}/type_generic_dark.svg", "OmniNote"),
            NodeBaseItem("Scene Graph", "Enable your to build subGraph", f"{ICON_PATH}/type_scene_graph_dark.svg", "Compound"),
            NodeBaseItem("Input", "Provide access to the inputs of the current compound", f"{ICON_PATH}/type_input_dark.svg", "Input"),
            NodeBaseItem("Output", "Provide access to the outputs of the current compound", f"{ICON_PATH}/type_input_dark.svg", "Output")
        ]

    def destroy(self):
        pass

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        # when input is None, it means the input item is the root layer, we return the group items
        if item is None:
            return [c for c in self._children if c.filtered]
        # when the input item is a type of GroupItem, we return its children items
        elif isinstance(item, GroupItem):
            return [c for c in item.children if c.filtered]
        return []

    def get_item_value_model_count(self, item):
        """The number of columns. There is only one column in our case"""
        return 1

    def get_item_value_model(self, item: NodeBaseItem, column_id: int):
        """
        Return value model. It's the object that tracks the specific value.
        In graph core, there are four value models defined for node registry model.
        """
        if column_id == self.Column.NAME.value:
            return item.name_model
        if column_id == self.Column.INFO.value:
            return item.info_model
        if column_id == self.Column.ICON.value:
            return item.icon_model
        if column_id == self.Column.TYPE.value:
            return item.type_model

    def get_drag_mime_data(self, item):
        """Returns data to be able to drage and drop this item somewhere. These are the information needed to create
        new node on graph"""
        data = {
            "node_type": self.get_item_value_model(item, self.Column.TYPE.value).as_string,
            "node_name": self.get_item_value_model(item, self.Column.NAME.value).as_string,
        }
        return json.dumps(data)

    def filter_by_text(self, filter_name_text: str):
        """Specify the filter string that is used to reduce the model"""
        for c in self._children:
            # we want the check to be case-insensitive
            c.prefilter(filter_name_text.lower())
        # redraw the entire graph
        self._item_changed(None)


class NodeRegistryQuickSearchModel(NodeRegistryModel):
    """
    The quick search node model that returns all the children.
    """

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        children = []

        # Bypass sections
        for section in super().get_item_children(item):
            children += super().get_item_children(section)

        return children

    def execute(self, item):
        """The user pressed enter"""
        # Mime Data has the information about USD types.
        data = self.get_drag_mime_data(item)
        if not data:
            return

        from .extension import ComfyUIEditorExtension

        ComfyUIEditorExtension.add_node(data)
