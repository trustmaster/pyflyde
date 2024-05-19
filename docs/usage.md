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

## Generating TS definitions for Flyde visual editor

Flyde visual editor is written for TypeScript runtime and is not aware of your Python nodes. To make your local nodes appear in the Flyde editor, you need to generate `.flyde.ts` files for them.

For example:

```bash
pyflyde gen mypackage/supermodule.py
```

will generate `mypackage/supermodule.flyde.ts` TypeScript defintions for Flyde using the contents of your `mypackage.submodule` module.

You should run `pyflyde gen` every time your create new modules containing PyFlyde nodes or whenever you update node signature (name, description, inputs, outputs, etc.).
