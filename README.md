# PyFlyde

![Build](https://github.com/trustmaster/pyflyde/actions/workflows/python-package.yml/badge.svg)

Python runtime for [Flyde](https://github.com/flydelabs/flyde) with Data Engineering emphasis.

![Example graph running K-means clustering with Pandas and Scikit-learn](https://github.com/trustmaster/pyflyde/blob/main/clustering_example.png?raw=true)

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
./flyde.py examples/HelloPy.flyde
```

### Using the visual editor

Install Flyde VSCode extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=flyde.flyde-vscode).

Whenever you change your component library classes or their interfaces, use flyde.py gen command to generate .flyde.ts definitions, e.g.:

```bash
./flyde.py gen examples/mylib/components.py
```

## Running a Machine Learning example

`Clustering.flyde` is a more complex example which uses Pandas and Scikit-Learn to run K-means clustering on a [wine clustering dataset from Kaggle](https://www.kaggle.com/harrywang/wine-dataset-for-clustering). It's a PyFlyde version of https://github.com/Shivangi0503/Wine_Clustering_KMeans.

To run this example, you need to install its dependencies first:

```bash
cd examples
pip install .
cd ..
```

After going back to the main folder you can run it with:

```bash
./flyde.py examples/Clustering.flyde
```

## Contributing

### Install dev dependencies

```bash
pip install .\[dev\]
```

### Run tests and coverage reports

To run tests only:

```bash
make test
```

TO run tests with coverage and see report:

```bash
make cover report
```
