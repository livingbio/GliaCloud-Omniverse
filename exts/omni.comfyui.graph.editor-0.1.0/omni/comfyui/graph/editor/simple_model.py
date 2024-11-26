from omni.kit.widget.graph.graph_model import GraphModel
from omni.kit.widget.graph import GraphModelBatchPositionHelper, AbstractBatchPositionGetter
from omni.kit.widget.graph import SelectionGetter, BackdropGetter
from typing import List, Any, Dict, Set, Tuple

from .nodes import (
    Node,
    Port,
    GraphNode,
    TextureNode,
    MDLNode,
    Backdrop,
    OmniNote,
    CompoundNode,
    RenderingNode,
    GeometryNode,
    TimeNode,
    AnimationNode,
    DebugNode,
    UINode,
    IONode,
    EventNode,
    MathNode,
)
import json


class DescendantGetter(AbstractBatchPositionGetter):
    """Helper to get the nodes that are descendatns of the input node"""

    def __init__(self, model: GraphModel):
        super().__init__(model)

    def __call__(self, drive_item: Any):
        model = self.model
        if model and model.move_descendant:
            descendants = []

            if isinstance(drive_item, Node):
                node = drive_item
            elif isinstance(drive_item, Port):
                node = drive_item.node
            else:  # could be backdrop or note, return early for that
                return descendants

            current_graph = model.current_graph

            def _get_descendant(descendants, node: Node):
                for port in node.in_ports + node.out_ports:
                    for input in port.inputs + port.outputs:
                        input_node = input.node
                        # this could be a new created input port
                        if input_node is None and isinstance(input, Port):
                            descendants.append(input)
                        # we need the nodes to be on the current graph. Other descendants we don't care here
                        elif input_node in current_graph.children():
                            descendants.append(input_node)
                            _get_descendant(descendants, input_node)
                        # this is a compound Input node, so we terminate the recursion here
                        elif input_node == current_graph:
                            descendants.append(input)

            _get_descendant(descendants, node)
            return descendants


class SimpleGraphModel(GraphModel, GraphModelBatchPositionHelper):
    """Simple model with few nodes to demo and test the Delegate. This manages all the data for the graph."""

    def __init__(self, graph_root: GraphNode, graph_data: Dict = None):
        super().__init__()
        # all the nodes in the graph
        self._nodes: List[Node] = []
        # all the selected nodes in the current graph
        self._selected_nodes: List[Node] = []

        # when that feature is on, and we are moving a node, all the input nodes of the node will also be moved
        self.move_descendant: bool = False

        # whether enabling multi-selection
        self.append_selection_mode: bool = False
        # the current active node
        self._current_active_node: Node = None
        # the current selected nodes map which has Node as the key and postion as the value
        self._current_selected_nodes: Dict[Node, Tuple[float]] = {}

        # for node resizing
        self.__sizes_on_begin = {}

        # this is a dictionary from dest Port to source str path
        self.__connections: Dict[Port, str] = {}

        # this is a dictionary contains the node as the key and connected ports as the path
        self.__connected_ports: Dict[Node, Set[Port]] = {}
        self._graph_root = graph_root

        # this is a dictionary from item str path to item, the item could be Port or Node
        self.__graph_map: Dict[str, Any] = {}
        # adding the graph root
        self.__graph_map[graph_root.path] = graph_root

        # the current graph, it could be the graph root, or navigated to some compound
        self.__current_graph = None

        self.__selection_getter_sub = self.add_get_moving_items_fn(SelectionGetter(self))
        self.__backdrop_getter_sub = self.add_get_moving_items_fn(
            BackdropGetter(self, lambda item: self[item].type == "Backdrop")
        )
        self.__descendant_getter_sub = self.add_get_moving_items_fn(DescendantGetter(self))

        # use the input graph_data to build the graph
        if graph_data:
            self.__build_graph(graph_data)

    def destroy(self):
        super().destroy()
        self._nodes = []
        self._selected_nodes = []

        self._current_active_node = None
        self._current_selected_nodes = {}

        self.__selection_getter_sub = None
        self.__backdrop_getter_sub = None
        self.__descendant_getter_sub = None

        self.__sizes_on_begin = {}

        self._graph_root = None
        self.__connections = {}
        self.__graph_map = {}

        self.__current_graph = None

    def __build_graph(self, data):
        self.__build_node(data, self._graph_root)
        # build all the connections afterwards, since without define all the ports, we can't work on connections
        for dest_port, src_strs in self.__connections.items():
            for src_str in src_strs:
                src_port = self.__graph_map.get(src_str, None)
                if src_port is not None:
                    if dest_port.is_input:
                        dest_port.inputs.append(src_port)
                    else:
                        dest_port.outputs.append(src_port)

                    # connected_ports are used for delegate to draw the visual ports when the nodes are CLOSED
                    # we don't add the subgraph connection when it's the `creating new port` connection,
                    # since that subgraph port is not yet connected to external nodes.
                    if dest_port.is_input != src_port.is_input:
                        dest_node = dest_port.node
                        self.__connected_ports[dest_node] = self.__connected_ports.get(dest_node, set()) | {dest_port}
                        src_node = src_port.node
                        self.__connected_ports[src_node] = self.__connected_ports.get(src_node, set()) | {src_port}

    def create_new_node(self, node_name, node_type, parent, position=None):
        """create new node based on node types"""
        if node_type == "Texture":
            node = TextureNode(node_name, parent)
        elif node_type == "Material":
            node = MDLNode(node_name, parent)
        elif node_type == "Backdrop":
            node = Backdrop(node_name, parent)
        elif node_type == "OmniNote":
            node = OmniNote(node_name, parent)
        elif node_type == "Compound":
            node = CompoundNode(node_name, parent)
        elif node_type == "Rendering":
            node = RenderingNode(node_name, parent)
        elif node_type == "Geometry":
            node = GeometryNode(node_name, parent)
        elif node_type == "Time":
            node = TimeNode(node_name, parent)
        elif node_type == "Animation":
            node = AnimationNode(node_name, parent)
        elif node_type == "Debug":
            node = DebugNode(node_name, parent)
        elif node_type == "UI":
            node = UINode(node_name, parent)
        elif node_type == "IO":
            node = IONode(node_name, parent)
        elif node_type == "Event":
            node = EventNode(node_name, parent)
        elif node_type == "Math":
            node = MathNode(node_name, parent)
        else:
            node = Node(node_name, parent)

        # cache default ports
        for port in node.in_ports + node.out_ports:
            port.node = node
            self.__graph_map[port.path] = port

        parent.add_child(node)
        self.__graph_map[node.path] = node
        if position:
            node.position = position
        return node

    def __build_node(self, graph_data: Dict, parent):
        nodes_data = graph_data.get("nodes", [])
        # build all the nodes and ports recursively
        for node_data in nodes_data:
            for node_name, data in node_data.items():
                node_type = data.get("type", "Node")
                position = data.get("position", None)
                if position:
                    position = eval(position)
                node = self.create_new_node(node_name, node_type, parent, position)

                state = data.get("state", "OPEN")
                if state == "OPEN":
                    node.state = GraphModel.ExpansionState.OPEN
                elif state == "MINIMIZED":
                    node.state = GraphModel.ExpansionState.MINIMIZED
                else:
                    node.state = GraphModel.ExpansionState.CLOSED

                ui_name = data.get("ui_name", None)
                if ui_name:
                    node.ui_name = ui_name
                # need to build more nodes if there are Compound node
                if node_type == "Compound":
                    self.__build_node(data, node)
                elif node_type in ["Backdrop", "OmniNote"]:
                    display_color = data.get("display_color", None)
                    if display_color:
                        node.display_color = eval(display_color)
                    node_size = data.get("size", None)
                    if node_size:
                        node.size = eval(node_size)

                # build port fot the node
                self.__build_port(data, node, node)

    def get_next_free_name(self, children, node_type: str):
        """get the next unique node name in the curernt graph level"""
        base_name = node_type
        proposed_name = base_name
        proposed_id = 0
        while proposed_name in children:
            proposed_id += 1
            proposed_name = f"{base_name}{proposed_id}"
        return proposed_name

    def create_node(self, node_type: str, position: Tuple[float]):
        """create a new node with input type and position"""
        if self.current_graph:
            nodes = [node.name for node in self.current_graph.children()]
            node_name = self.get_next_free_name(nodes, node_type)
            self.create_new_node(node_name, node_type, self.current_graph, position)
            self._item_changed(None)

    def __build_port(self, data: Dict, node: Node, parent):
        """
        parent could be node or port
        """
        if parent is None:
            return

        is_sub_port = True if isinstance(parent, Port) else False

        # cache default ports
        if not is_sub_port:
            ports = parent.in_ports + parent.out_ports
        else:
            ports = parent.children
        # cache existing ports to model
        for port in ports:
            port.node = node
            self.__graph_map[port.path] = port

        ports_data = data.get("ports", [])
        for port_data in ports_data:
            for port_name, data in port_data.items():
                port_path = parent.path + ":" + port_name.split(":")[-1]
                if port_path in self.__graph_map:
                    port = self.__graph_map[port_path]
                else:
                    port_type = data.get("type", None)
                    if port_type is None:
                        continue
                    port = Port(port_name, port_type, parent)
                    port.node = node
                    self.__graph_map[port.path] = port

                    if is_sub_port:
                        parent.children.append(port)
                    else:
                        if port.is_input:
                            parent.in_ports.append(port)
                        else:
                            parent.out_ports.append(port)

                state = data.get("state", "CLOSED")
                if state == "OPEN":
                    port.state = GraphModel.ExpansionState.OPEN
                elif state == "MINIMIZED":
                    port.state = GraphModel.ExpansionState.MINIMIZED
                else:
                    port.state = GraphModel.ExpansionState.CLOSED

                # check the connection
                for src in data.get("inputs", []) + data.get("outputs", []):
                    self.__connections[port] = self.__connections.get(port, []) + [src]

                # iteratively build port, there could be sub ports for port
                self.__build_port(data, node, port)

    def can_connect(self, source, target):
        """Return if it's possible to connect source to target"""
        if source and target:
            return source.type == target.type

    def write_port(self, port):
        """write port to json file"""
        data = {}
        port_data = {}
        data[port.name] = port_data
        port_data["type"] = port.type
        port_data["state"] = port.state.name
        if port.position:
            port_data["position"] = str(port.position)

        inputs = port.inputs
        if len(inputs) > 0:
            port_data["inputs"] = []
            for input in inputs:
                port_data["inputs"].append(input.path)

        outputs = port.outputs
        if len(outputs) > 0:
            port_data["outputs"] = []
            for output in outputs:
                port_data["outputs"].append(output.path)

        subports = port.children
        if len(subports) > 0:
            port_data["ports"] = []
            for subport in subports:
                port_data["ports"].append(self.write_port(subport))

        return data

    def write_node(self, node):
        """write node to json file"""
        data = {}
        node_data = {}
        data[node.name] = node_data
        node_type = node.type
        node_data["type"] = node_type
        node_data["ui_name"] = node.ui_name
        node_data["state"] = node.state.name

        if node.position:
            node_data["position"] = str(node.position)
        if node_type == "Compound":
            node_data["nodes"] = []
            for child in node._children:
                node_data["nodes"].append(self.write_node(child))
        # save display color and size for backdrop or note node
        elif node_type in ["Backdrop", "OmniNote"]:
            node_data["display_color"] = str(node.display_color)
            # size have px as the appendix, remove it before saving it
            node_data["size"] = str((float(node.size[0]), float(node.size[1])))

        node_data["ports"] = []
        for port in node.in_ports + node.out_ports:
            node_data["ports"].append(self.write_port(port))
        return data

    def write_graph(self, file_path):
        """write graph to json file"""
        data = {}
        graph_data = {}
        data[self._graph_root.name] = graph_data
        graph_data["type"] = "Graph"
        graph_data["nodes"] = []

        for child in self._graph_root._children:
            graph_data["nodes"].append(self.write_node(child))

        with open(file_path, "w") as fp:
            json.dump(data, fp)

    @property
    def current_graph(self):
        """return the current graph, could be the root graph or compound"""
        return self.__current_graph

    @current_graph.setter
    def current_graph(self, value):
        """set the current graph, this is used for graph widget to set the current graph for model"""
        self.__current_graph = value

    ################################################################
    # API OVERLOAD
    ################################################################

    @property
    def nodes(self, item=None):
        """the nodes of the input item. The return type defines the node type for the Graph.
        For example here, we return None or [Nodes], so the type of node in our graph is Node"""
        # when the node is None, we return the graph level node
        if item is None:
            return self._graph_root

        # when the input item root, we return all the nodes exist on the current graph
        if item == self._graph_root:
            return [
                child
                for child in self._graph_root.children()
                if isinstance(child, Node) or isinstance(child, Backdrop) or isinstance(child, OmniNote)
            ]

        # when the input item root, we return all the nodes exist on the current compound node
        if item.type == "Compound":
            return item.children().copy()

        return None

    @property
    def name(self, item):
        """name of the item, the item here could be Node or Port"""
        if item:
            return item.ui_name
        return ""

    @name.setter
    def name(self, value, item):
        if isinstance(item, Node) or isinstance(item, Backdrop) or isinstance(item, OmniNote):
            item.ui_name = value
            self._item_changed(item)

    @property
    def type(self, item):
        """type of the item, the item here could be Node or Port"""
        return item.type

    @property
    def inputs(self, item):
        """inputs of the item defines the connection inputs of the item. Thus, we only care about Port here"""
        if isinstance(item, Node):
            return None

        if item.is_input:
            return item.inputs

        return None

    @inputs.setter
    def inputs(self, value, item):
        """setting the inputs of item. This is called while we connect/disconnect a port from inputs, the value could
        be [] (disconnection in the case) or [Ports] (connection in this case)"""

        # disconnection
        if len(value) == 0:
            if isinstance(item, Port):
                if len(item.inputs) > 0:
                    item.inputs.clear()
                elif len(item.outputs) > 0:
                    item.outputs.clear()
        else:
            # when the item is not a Port, but a CompoundNode,
            # it means that we are connecting a port to the Output node of
            # a compoundNode. In this case, we need to create a new output port for the node
            source = value[0]
            if isinstance(item, CompoundNode):
                ports = [port.name for port in item.out_ports]
                new_port_name = self.get_next_free_name(ports, source.name)
                new_port = Port(new_port_name, source.type, item)
                item.out_ports.append(new_port)
                # We are connecting to the new Port
                new_port.outputs.append(source)
                new_port.node = item
            # if the source is a CompoundNode, then we are connection a port to the Input node of a CompoundNode.
            # we need to create a new input port
            elif isinstance(source, CompoundNode):
                ports = [port.name for port in source.in_ports]
                new_port_name = self.get_next_free_name(ports, item.name)
                new_port = Port(new_port_name, item.type, source)
                source.in_ports.append(new_port)
                # add connection
                item.inputs.append(new_port)
                new_port.node = source
            else:
                # both ports exist and types align, just do the connection
                if self.can_connect(source, item):
                    if item.is_input:
                        item.inputs.append(source)
                    else:
                        item.outputs.append(source)
                    self.__connected_ports[item.node] = self.__connected_ports.get(item.node, set()) | {item}
                    self.__connected_ports[source.node] = self.__connected_ports.get(source.node, set()) | {source}
        self._item_changed(None)

    @property
    def outputs(self, item):
        """outputs of the item defines the connection outputs of the item. Thus, we only care about Port here
        In our case, the outputs are only the conneciton between a port to a Output port of a Compound node
        """
        if isinstance(item, Node):
            return None

        if not item.is_input:
            return item.outputs

        return None

    @property
    def ports(self, item=None):
        if item is None:
            return None

        # if input is a Port, return its sub ports
        if isinstance(item, Port):
            if len(item.children):
                return item.children
            else:
                return None
        # if it is a Backdrop or Note, there are no ports
        if isinstance(item, Backdrop) or isinstance(item, OmniNote):
            return []

        return item.in_ports + item.out_ports

    @property
    def connected_ports(self, item=None):
        """Get the connected ports for the input node"""
        if not isinstance(item, Node):
            return set()

        return self.__connected_ports.get(item, set())

    @ports.setter
    def ports(self, value, item=None):
        """Set the node ports. In this example, it is
        only used for CompoundNode to moves the ports
        """
        if not isinstance(item, CompoundNode):
            return

        item.in_ports = []
        item.out_ports = []
        for port in value:
            if port.is_input:
                item.in_ports.append(port)
            else:
                item.out_ports.append(port)
        self._item_changed(item)

    @property
    def expansion_state(self, item=None):
        """the expansion state of a node or a port"""
        if isinstance(item, Port) or isinstance(item, Node):
            return item.state
        else:  # could be the empty port of Compound node
            return GraphModel.ExpansionState.OPEN

    @expansion_state.setter
    def expansion_state(self, value: GraphModel.ExpansionState, item: Any = None):
        """set the expansion state of a node or a port"""
        item.state = value
        self._item_changed(None)

    @property
    def stacking_order(self, item):
        """Allows to draw backdrops in background, so that we can see the nodes belong to the backdrop"""
        if self[item].type == "Backdrop":
            return -1
        return 1

    @property
    def selection(self):
        """return the selected node"""
        return self._selected_nodes

    @selection.setter
    def selection(self, value: List[Node]):
        """set the selection"""
        if self.append_selection_mode:
            self._selected_nodes = self._selected_nodes + value
        else:
            if value and value != self._selected_nodes:
                self._selected_nodes = value
            elif len(value) == 0:
                self._selected_nodes = []

        self._selection_changed()

    def delete_selection(self):
        if not self._selected_nodes:
            return
        for node in self._selected_nodes:
            if node in self.__current_graph.children():
                self.__current_graph.children().remove(node)
            else:  # this is an input/output node
                # since there is no way to know the selection is an input or output
                print("Deleting an Input/Output Node is currently not supported")
        self._item_changed(None)

    @property
    def size(self, item):
        """return node's size"""
        return item.size

    @size.setter
    def size(self, value, item=None):
        """resize the input node"""
        # we use self.__sizes_on_begin to reduce ops needed
        if item.path in self.__sizes_on_begin:
            item.size = value

    def size_begin_edit(self, item):
        """initial size of the input item"""
        self.__sizes_on_begin[item.path] = self[item].size

    def size_end_edit(self, item):
        """finish editing size"""
        self.__sizes_on_begin.pop(item.path)

    @property
    def description(self, item):
        """node description, mainly for backdrop and note nodes"""
        if hasattr(item, "description"):
            return item.description

    @description.setter
    def description(self, value, item=None):
        """set node description, mainly for backdrop and note nodes"""
        if hasattr(item, "description"):
            item.description = value

    @property
    def display_color(self, item):
        """node display color, mainly for backdrop node"""
        return item.display_color

    @display_color.setter
    def display_color(self, value, item=None):
        """set node display color, mainly for backdrop node"""
        item.display_color = value

    # Position Settings and Support for Backdrop

    @property
    def position(self, item):
        """item position: item could be either Node or Port (Input/Output node)"""
        return item.position

    @position.setter
    def position(self, value, item=None):
        """set the position"""
        self.batch_set_position(value, item)
        prev_position = item.position
        if not value:
            item.position = None
            self._item_changed(item)
        else:
            if prev_position != value[0]:
                item.position = value
                self._item_changed(item)

    def position_begin_edit(self, item):
        # initial position of the input item
        self.batch_position_begin_edit(item)

    def position_end_edit(self, item):
        """finishing editing nodes"""
        self.batch_position_end_edit(item)

    @property
    def preview(self, item: Node):
        """preview data info, for delegate query"""
        if isinstance(item, Node):
            return item.preview_data

        return None

    @property
    def preview_state(self, item: Node) -> GraphModel.ExpansionState:
        """preview state info, for delegate query"""
        if isinstance(item, MDLNode) or isinstance(item, TextureNode):
            return item.preview_state

        return GraphModel.ExpansionState.CLOSED

    @preview_state.setter
    def preview_state(self, value, item: Node) -> GraphModel.ExpansionState:
        if isinstance(item, MDLNode) or isinstance(item, TextureNode):
            item.preview_state = value
        else:
            print(f"Node Type {type(item)} doesn't support preview_state")
