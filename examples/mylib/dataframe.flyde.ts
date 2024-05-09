import { CodeNode } from "@flyde/core";

export const LoadDataset: CodeNode = {
  id: "LoadDataset",
  description: "Loads a dataset from a file into a DataFrame.",
  inputs: {
    file_path: { description: "The path to the file containing the dataset" }
  },
  outputs: {
    dataframe: { description: "The loaded dataframe" }
  },
  run: () => { return; },
};

export const Scale: CodeNode = {
  id: "Scale",
  description: "Scales the features of a dataframe with a scikit-learn StandardScaler.",
  inputs: {
    dataframe: { description: "The dataframe to scale" }
  },
  outputs: {
    scaled_dataframe: { description: "The scaled dataframe" }
  },
  run: () => { return; },
};

