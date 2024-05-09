"""Components for working with generic Pandas dataframes."""

import pandas as pd  # type: ignore

from sklearn.preprocessing import StandardScaler  # type: ignore

from flyde.node import Component
from flyde.io import Input, Output


class LoadDataset(Component):
    """Loads a dataset from a file into a DataFrame."""

    inputs = {
        "file_path": Input(
            description="The path to the file containing the dataset", type=str
        ),
    }
    outputs = {
        "dataframe": Output(description="The loaded dataframe", type=pd.DataFrame),
    }

    def process(self, file_path: str) -> dict[str, pd.DataFrame]:
        dataframe = pd.read_csv(file_path)
        return {"dataframe": dataframe}


class Scale(Component):
    """Scales the features of a dataframe with a scikit-learn StandardScaler."""

    inputs = {
        "dataframe": Input(description="The dataframe to scale", type=pd.DataFrame),
    }
    outputs = {
        "scaled_dataframe": Output(
            description="The scaled dataframe", type=pd.DataFrame
        ),
    }

    def process(self, dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        scaler = StandardScaler()
        scaled_dataframe = pd.DataFrame(
            scaler.fit_transform(dataframe), columns=dataframe.columns
        )
        return {"scaled_dataframe": scaled_dataframe}
