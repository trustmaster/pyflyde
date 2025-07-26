# CLI tool usage

## Running Flyde flows

You can use `pyflyde` tool to run a `.flyde` flow:

```bash
pyflyde run examples/HelloWorld.flyde
```

You can omit the `run` command because it is the default one. The following command is equivalent to the above:

```bash
pyflyde examples/HelloWorld.flyde
```

## Generating component definitions for Flyde visual editor

To make your Python nodes appear in the Flyde visual editor, you need to generate `flyde-nodes.json` metadata files for them.

Generate JSON definitions for a directory:

```bash
pyflyde gen mypackage/
```

This will recursively scan all `.py` files in the directory and its subdirectories, then generate a `flyde-nodes.json` file in the specified directory containing metadata for all PyFlyde components found. The paths in the generated JSON file are relative to the directory containing the `flyde-nodes.json` file, making the component library portable.

For example, if you have components in:
- `mypackage/components.py`
- `mypackage/utils/helpers.py`

The generated `flyde-nodes.json` will reference them as:
- `custom://components.py/ComponentName`
- `custom://utils/helpers.py/HelperComponentName`

You should run `pyflyde gen` every time you create new modules containing PyFlyde nodes or whenever you update node signatures (name, description, inputs, outputs, etc.).
