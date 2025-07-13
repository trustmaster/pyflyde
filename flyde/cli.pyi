from _typeshed import Incomplete
from flyde.flow import Flow as Flow, add_folder_to_path as add_folder_to_path
from flyde.node import Component as Component, SUPPORTED_MACROS as SUPPORTED_MACROS

log_level: Incomplete
logger: Incomplete

def py_path_to_module(py_path: str) -> str: ...
def convert_class_name_to_display_name(class_name: str) -> str:
    """Convert a class name like 'MyCustomNode' to 'My Custom Node'."""
def is_stdlib_node(node_name: str) -> bool:
    """Check if a node name matches a stdlib node."""
def collect_components_from_directory(directory_path: str) -> dict:
    """Collect all Component subclasses from .py files in a directory."""
def generate_node_json(node_name: str, component_class, file_path: str = '') -> dict:
    """Generate JSON structure for a single component."""
def gen_json(directory_path: str):
    """Generate JSON file for all components in a directory."""
def main() -> None: ...
