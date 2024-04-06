import { CodeNode } from "@flyde/core";

export const PCA2: CodeNode = {
  id: "PCA2",
  description: "Performs PCA on a dataframe and returns the first two principal components.",
  inputs: { 
    scaled_dataframe: {"description": "The scaled dataframe to reduce"}
 },
  outputs: { 
    pca_components: {"description": "The first two principal components"}
 },
  run: () => { return; },
};

export const KMeansNClusters: CodeNode = {
  id: "KMeansNClusters",
  description: "Finds the optimal number of clusters for K-means clustering using silhouette method.",
  inputs: { 
    scaled_dataframe: {"description": "The scaled dataframe to cluster"},
    max_clusters: {"description": "The maximum number of clusters to consider"}
 },
  outputs: { 
    n_clusters: {"description": "The optimal number of clusters"}
 },
  run: () => { return; },
};

export const KMeansCluster: CodeNode = {
  id: "KMeansCluster",
  description: "Clusters the dataframe using K-means clustering.",
  inputs: { 
    scaled_dataframe: {"description": "The scaled dataframe to cluster"},
    n_clusters: {"description": "The number of clusters"}
 },
  outputs: { 
    kmeans_result: {"description": "K-means clustering result"}
 },
  run: () => { return; },
};

export const Visualize: CodeNode = {
  id: "Visualize",
  description: "Visualizes the clustered dataframe.",
  inputs: { 
    pca_components: {"description": "The first two principal components"},
    pca_centroids: {"description": "The centroids in PCA space"},
    kmeans_result: {"description": "K-means clustering result"}
 },
  outputs: {  },
  run: () => { return; },
};

