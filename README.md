# PyFlyde

Python runtime for [Flyde](https://github.com/flydelabs/flyde) with Data Engineering emphasis.

## PoC warning

This is a proof-of-concept and not a final implementation. Structure and API may change drastically before public release.

## Getting started

You need Python 3.9+ installed on your machine to run PyFlyde.

First, you need to install its dependencies:

```bash
pip install .
```

Then you can run the Hello World example:

```bash
./flyde.py HelloPy.flyde
```

### Using the visual editor

To make your flows show in Flyde visual editor, you currently have to install Flyde TypeScript dependencies:

```bash
npm install
```

Whenever you change your component library classes or their interfaces, use flyde.py gen command to generate .flyde.ts definitions, e.g.:

```bash
./flyde.py gen mylib.components
```
