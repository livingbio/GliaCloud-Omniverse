
from omni.kit.widget.graph.graph_model import GraphModel
from typing import List
from pathlib import Path
import carb

CURRENT_PATH = Path(carb.tokens.get_tokens_interface().resolve("${omni.kit.graph.editor.example}"))
FILE_PATH1 = CURRENT_PATH.absolute().resolve().joinpath("data/Carpet_Cream.mdl.png")
FILE_PATH2 = CURRENT_PATH.absolute().resolve().joinpath("data/Carpet_Gray.mdl.png")


class Port():
    """port class, e.g. attributes of nodes"""

    def __init__(self, _name: str, _type: str, _parent):
        # parent could be Port or Node, we require a parent for each Port when define it
        # it can't exist by its own
        if _parent is None or not (isinstance(_parent, Port) or isinstance(_parent, Node)):
            return

        self.is_input = True
        self.name = _name
        self.ui_name = self.name
        # use name to differenciate the inputs and outputs
        if _name.startswith("input:"):
            # strip off "inputs:"
            self.ui_name = _name[6:]
        elif _name.startswith("output:"):
            self.is_input = False
            # strip off "outputs:"
            self.ui_name = _name[7:]

        # port path contains the port path
        self.path = _parent.path + ":" + self.ui_name

        self.type = _type
        # node of the port
        self.node = None
        self.position = None
        # input connections
        self.inputs = []
        # output connection
        self.outputs = []

        self.children = []
        # expansion states
        self.state: GraphModel.ExpansionState = GraphModel.ExpansionState.CLOSED


class Node():
    """node base class"""

    def __init__(self, name: str, parent=None):
        # parent could be CompoundNode or Graph, since GraphNode itself is also a type of Node, parent is optional
        self.name = name
        self._ui_name = name
        self.parent = parent
        self.path = name if parent is None else parent.path + ":" + name

        # we give one default input Port
        self.group_port = Port("input:Group Input", "group", self)
        self.group_port.children = [Port("input:child1", "int", self.group_port), Port("input:child2", "int", self.group_port)]

        self._in_ports = [Port("input:Default Input", "str", self), self.group_port]
        # we give one default output Port
        self._out_ports = [Port("output:Default Output", "str", self)]

        self.type = "Function"
        self.state: GraphModel.ExpansionState = GraphModel.ExpansionState.OPEN
        self.position = None
        self.display_color = None
        self.preview_data = None
        self.size = None

    @property
    def ui_name(self):
        return self._ui_name

    @ui_name.setter
    def ui_name(self, name):
        self._ui_name = name

    @property
    def in_ports(self):
        return self._in_ports

    @in_ports.setter
    def in_ports(self, values):
        self._in_ports = values

    @property
    def out_ports(self):
        return self._out_ports

    @out_ports.setter
    def out_ports(self, values):
        self._out_ports = values


class CompoundNode(Node):
    """The subgraph nodes. It could contain many different types of nodes and more compounds nodes."""
    def __init__(self, name: str, parent = None):
        super().__init__(name, parent)
        self._children: List[Node] = []
        self.type = "Compound"

        # redefine the ports to be empty, we don't want Compound node to have default port
        self._in_ports = []
        self._out_ports = []

    def add_children(self, nodes: List[Node]):
        self._children.extend(nodes)

    def add_child(self, node: Node):
        self._children.append(node)

    def children(self):
        return self._children


class GraphNode(CompoundNode):
    """The root graph node. It could contain many different types of nodes and compound nodes.
    Functionnally similar with Compound Node, but only one per graph. Therefore, we can't create Graph typed node
    from node registry model"""
    def __init__(self, name: str):
        super().__init__(name)

        self._children: List[Node] = []
        self.type = "Graph"


class TextureNode(Node):
    """Special texture node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Texture"
        # extra data for delegate to use
        self.preview_data = str(FILE_PATH2)
        self.preview_state = GraphModel.ExpansionState.MINIMIZED

        # we give one default input Port
        self._in_ports = [Port("input:in_texture", "texture", self), Port("input:mult", "float", self), Port("input:Default Input", "str", self)]
        # we give one default output Port
        self._out_ports = [Port("output:out_texture", "texture", self), Port("output:Default Output", "str", self)]


class RenderingNode(Node):
    """Special texture node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Rendering"
        # we give one default input Port
        self._in_ports = [Port("input:sample", "int", self), Port("input:resolution", "int", self), Port("input:in_texture", "texture", self)]
        # we give one default output Port
        self._out_ports = [Port("output:out_texture", "texture", self)]

class GeometryNode(Node):
    """Special texture node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Geometry"
        # we give one default input Port
        self._in_ports = [Port("input:num_faces", "int", self), Port("input:num_vertices", "int", self)]
        # we give one default output Port
        self._out_ports = [Port("output:asset", "asset", self)]


class TimeNode(Node):
    """Special texture node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Time"
        # we give one default input Port
        self._in_ports = [Port("input:seconds", "float", self)]
        # we give one default output Port
        self._out_ports = [Port("output:time_out", "float", self)]


class AnimationNode(Node):
    """Special animation node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Animation"
        # we give one default input Port
        self._in_ports = [Port("input:asset", "asset", self), Port("input:time", "float", self)]
        # we give one default output Port
        self._out_ports = [Port("output:num_frames", "int", self), Port("output:num_skeletons", "int", self), Port("output:is_live", "bool", self)]

class DebugNode(Node):
    """Special debug node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Debug"
        # we give one default input Port
        self._in_ports = [Port("input:in", "str", self), Port("input:is_debug", "bool", self)]
        # we give one default output Port
        self._out_ports = [Port("output:out", "str", self)]

class MathNode(Node):
    """Special math node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Math"
        # we give one default input Port
        self._in_ports = [Port("input:in1", "int", self), Port("input:in2", "float", self)]
        # we give one default output Port
        self._out_ports = [Port("output:out1", "float", self), Port("output:out2", "int", self)]


class UINode(Node):
    """Special UI node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "UI"
        self._in_ports = [Port("input:in_color", "color", self), Port("input:is_ui", "bool", self)]
        self._out_ports = [Port("output:out1", "asset", self)]

class IONode(Node):
    """Special IO node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "IO"


class EventNode(Node):
    """Special event node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Event"
        self._out_ports = [Port("output:time", "float", self)]

class MDLNode(Node):
    """Special MDL node"""
    def __init__(self, name: str, parent):
        super().__init__(name, parent)
        self.type = "Material"
        # extra data for delegate to use
        self.preview_data = str(FILE_PATH1)
        self.preview_state = GraphModel.ExpansionState.MINIMIZED

        # we give one default input Port
        self._in_ports = [Port("input:in_material", "color", self), Port("input:Default Input", "str", self)]
        # we give one default output Port
        self._out_ports = [Port("output:out_material", "color", self), Port("output:Default Output", "str", self)]


class Backdrop():
    """Back drop node"""
    def __init__(self, name: str, parent):
        self.name = name
        self.ui_name = name
        self.type = "Backdrop"
        self.state = GraphModel.ExpansionState.OPEN
        self.position = (-1400, -300)
        self.description = "This is a Backdrop"
        self.size = (800, 400)
        self.display_color = (0.3, 0.6, 0.2)
        self.path = self.name if parent is None else parent.path + ":" + self.name
        self.in_ports = []
        self.out_ports = []
        self.parent = parent


class OmniNote():
    """Note node"""
    def __init__(self, name: str, parent):
        self.name = name
        self.ui_name = name
        self.type = "OmniNote"
        self.state = GraphModel.ExpansionState.OPEN
        self.position = (-1400, -300)
        self.description = "Test Note"
        self.size = (200, 200)
        self.display_color = (0.9, 0.85, 0.65)
        self.path = self.name if parent is None else parent.path + ":" + self.name
        self.in_ports = []
        self.out_ports = []
        self.parent = parent
