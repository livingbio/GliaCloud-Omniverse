from omni.kit.graph.editor.example.graph_widget import GraphWidget
from omni.ui.tests.test_base import OmniUiTest
from pathlib import Path
import omni.kit
import omni.ui as ui
import carb

CURRENT_PATH = Path(carb.tokens.get_tokens_interface().resolve("${omni.kit.graph.editor.example}"))
FILE_PATH = CURRENT_PATH.absolute().resolve().joinpath("graphs/example.json")


class TestModel(OmniUiTest):
    # Before running each test
    async def setUp(self):
        await super().setUp()
        self._golden_img_dir = CURRENT_PATH.absolute().resolve().joinpath("data/tests")

    # After running each test
    async def tearDown(self):
        self._golden_img_dir = None
        await super().tearDown()

    async def test_general(self):
        """test the general widget"""
        await self.create_test_area(width=1950, height=1050)
        graph_window = ui.Window("DelegateTest", width=1950, height=1050)
        graph_widget = None
        with graph_window.frame:
            graph_widget = GraphWidget()
        # wait a few frames for the GraphView to initialize the model
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()

        graph_widget.read_graph(FILE_PATH)

        for _ in range(30):
            await omni.kit.app.get_app().next_update_async()

        await self.finalize_test(golden_img_dir=self._golden_img_dir)

        if graph_widget:
            graph_widget.destroy()
        graph_widget = None
        graph_window = None

    async def test_deletion(self):
        """test the compound deletion"""
        await self.create_test_area(width=1950, height=1050)
        graph_window = ui.Window("DeletionTest", width=1950, height=1050)
        graph_widget = None
        with graph_window.frame:
            graph_widget = GraphWidget()
        # wait a few frames for the GraphView to initialize the model
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()

        graph_widget.read_graph(FILE_PATH)

        for _ in range(30):
            await omni.kit.app.get_app().next_update_async()

        root_item = graph_widget._graph_root
        nodes = root_item.children()
        compound_nodes = [n for n in nodes if n.type == "Compound"]

        compound_node_names = [n.name for n in compound_nodes]

        self.assertEqual(set(compound_node_names), {'One Compound', 'Other Compound'})

        # goes into the Compound node
        graph_widget.set_current_compound(compound_nodes[0])
        self.assertEqual(graph_widget._graph_model.current_graph, compound_nodes[0])

        # goes back to the graph root again
        graph_widget.set_current_compound(root_item)
        self.assertEqual(graph_widget._graph_model.current_graph, root_item)

        graph_widget._graph_model.selection = compound_nodes
        graph_widget._graph_model.delete_selection()

        # check the children again and verify the compounds node have been removed
        nodes = root_item.children()
        compound_nodes = [n for n in nodes if n.type == "Compound"]
        self.assertEqual(len(compound_nodes), 0)

        for _ in range(30):
            await omni.kit.app.get_app().next_update_async()

        await self.finalize_test(golden_img_dir=self._golden_img_dir, threshold=100)

        if graph_widget:
            graph_widget.destroy()
        graph_widget = None
        graph_window = None
