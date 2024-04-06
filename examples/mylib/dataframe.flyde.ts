import { CodeNode } from "@flyde/core";

export const LoadDataset: CodeNode = {
  id: "LoadDataset",
  description: "Loads a dataset from a file into a DataFrame.",
  inputs: { 
    file_path: {"description": "The path to the file containing the dataset"}
 },
  outputs: { 
    dataframe: {"description": "The loaded dataframe"}
 },
  run: () => { return; },
};

export const Scale: CodeNode = {
  id: "Scale",
  description: "Scales the features of a dataframe with a scikit-learn StandardScaler.",
  inputs: { 
    dataframe: {"description": "The dataframe to scale"}
 },
  outputs: { 
    scaled_dataframe: {"description": "The scaled dataframe"}
 },
  run: () => { return; },
};

export const SplitRef2: CodeNode = {
  id: "SplitRef2",
  description: "Sends the reference to the same input dataframe to each of the outputs.\n    \n    This component should be used when downstream nodes don't modify the input dataframe.\n    ",
  inputs: { 
    dataframe: {"description": "The dataframe to split"}
 },
  outputs: { 
    dataframe1: {"description": "The first copy of the dataframe"},
    dataframe2: {"description": "The second copy of the dataframe"}
 },
  run: () => { return; },
};

export const SplitRef3: CodeNode = {
  id: "SplitRef3",
  description: "Sends the reference to the same input dataframe to each of the outputs.\n    \n    This component should be used when downstream nodes don't modify the input dataframe.\n    ",
  inputs: { 
    dataframe: {"description": "The dataframe to split"}
 },
  outputs: { 
    dataframe1: {"description": "The first copy of the dataframe"},
    dataframe2: {"description": "The second copy of the dataframe"},
    dataframe3: {"description": "The third copy of the dataframe"}
 },
  run: () => { return; },
};

export const SplitCopy3: CodeNode = {
  id: "SplitCopy3",
  description: "Sends copies of the input dataframe to each of the outputs.\n    \n    This component should be used when downstream nodes may modify the input dataframe.\n    ",
  inputs: { 
    dataframe: {"description": "The dataframe to split"}
 },
  outputs: { 
    dataframe1: {"description": "The first copy of the dataframe"},
    dataframe2: {"description": "The second copy of the dataframe"},
    dataframe3: {"description": "The third copy of the dataframe"}
 },
  run: () => { return; },
};

