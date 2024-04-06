"""Components for working with generic Pandas dataframes."""

import pandas as pd

from sklearn.preprocessing import StandardScaler

from flyde.node import Component
from flyde.io import Input, Output, InputMode

class LoadDataset(Component):
    """Loads a dataset from a file into a DataFrame."""
 
    inputs = {
        'file_path': Input(description='The path to the file containing the dataset', type=str),
    }
    outputs = {
        'dataframe': Output(description='The loaded dataframe', type=pd.DataFrame),
    }
    
    def process(self, file_path: str) -> dict[str, pd.DataFrame]:
        dataframe = pd.read_csv(file_path)
        return {'dataframe': dataframe}

class Scale(Component):
    """Scales the features of a dataframe with a scikit-learn StandardScaler."""

    inputs = {
        'dataframe': Input(description='The dataframe to scale', type=pd.DataFrame),
    }
    outputs = {
        'scaled_dataframe': Output(description='The scaled dataframe', type=pd.DataFrame),
    }
    
    def process(self, dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        scaler = StandardScaler()
        scaled_dataframe = pd.DataFrame(scaler.fit_transform(dataframe), columns=dataframe.columns)
        return {'scaled_dataframe': scaled_dataframe}

class SplitRef2(Component):
    """Sends the reference to the same input dataframe to each of the outputs.
    
    This component should be used when downstream nodes don't modify the input dataframe.
    """

    inputs = {
        'dataframe': Input(description='The dataframe to split'),
    }
    outputs = {
        'dataframe1': Output(description='The first copy of the dataframe'),
        'dataframe2': Output(description='The second copy of the dataframe'),
    }
    
    def process(self, dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        return {
            'dataframe1': dataframe,
            'dataframe2': dataframe,
    }

class SplitRef3(Component):
    """Sends the reference to the same input dataframe to each of the outputs.
    
    This component should be used when downstream nodes don't modify the input dataframe.
    """

    inputs = {
        'dataframe': Input(description='The dataframe to split'),
    }
    outputs = {
        'dataframe1': Output(description='The first copy of the dataframe'),
        'dataframe2': Output(description='The second copy of the dataframe'),
        'dataframe3': Output(description='The third copy of the dataframe'),
    }
    
    def process(self, dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        return {
            'dataframe1': dataframe,
            'dataframe2': dataframe,
            'dataframe3': dataframe,
    }

class SplitCopy3(Component):
    """Sends copies of the input dataframe to each of the outputs.
    
    This component should be used when downstream nodes may modify the input dataframe.
    """

    inputs = {
        'dataframe': Input(description='The dataframe to split'),
    }
    outputs = {
        'dataframe1': Output(description='The first copy of the dataframe'),
        'dataframe2': Output(description='The second copy of the dataframe'),
        'dataframe3': Output(description='The third copy of the dataframe'),
    }
    
    def process(self, dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        return {
            'dataframe1': dataframe.copy(),
            'dataframe2': dataframe.copy(),
            'dataframe3': dataframe.copy(),
    }
