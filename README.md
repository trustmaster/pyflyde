# PyFlyde

![Build](https://github.com/trustmaster/pyflyde/actions/workflows/python-package.yml/badge.svg)
[<img src="https://readthedocs.org/projects/pyflyde/badge/">](https://pyflyde.readthedocs.io/en/latest/)

Python runtime for [Flyde](https://github.com/flydelabs/flyde) with Data Engineering emphasis.

![Example graph running K-means clustering with Pandas and Scikit-learn](https://github.com/trustmaster/pyflyde/blob/main/clustering_example.png?raw=true)

## Getting started

You need Python 3.9+ installed on your machine to run PyFlyde.

Then you can install PyFlyde using pip:

```bash
pip install pyflyde
```

### Running the examples

You can copy `examples` folder from this repository to your local project to give it a try. Then you can run the example flow with:

```bash
pyflyde examples/HelloWorld.flyde
```


### Using the visual editor

Install Flyde VSCode extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=flyde.flyde-vscode). It will open existing `.flyde` files in the visual editor. You can call `Flyde: New Visual Flow` command in VSCode to create a new flow file.

You can browse the component library in the panel on the right. To see your local components click the "View all" button. They will appear under the "Current project". Note that PyFlyde doesn't implement all of the Flyde's stdlib components, only a few essential ones.

Whenever you change your component library classes or their interfaces, use `pyflyde gen` command to generate `.flyde.ts` definitions, e.g.:

```bash
pyflyde gen examples/mylib/components.py
```

Flyde editor needs `.flyde.ts` files in order to "see" your components.

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
pyflyde examples/Clustering.flyde
```

## Contributing

### Install dev dependencies

```bash
pip install .\[dev\]
```

### Run tests, linters and coverage reports

To run tests only:

```bash
make test
```

To run tests with coverage and see report:

```bash
make cover report
```

To run linters:

```bash
make lint
```
