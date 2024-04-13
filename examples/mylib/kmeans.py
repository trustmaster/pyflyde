"""Components for K-means clustering."""

import pandas as pd  # type: ignore
import matplotlib.pyplot as plt

from dataclasses import dataclass
from sklearn.decomposition import PCA  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from sklearn.metrics import silhouette_score  # type: ignore

from flyde.node import Component
from flyde.io import Input, Output, InputMode


class PCA2(Component):
    """Performs PCA on a dataframe and returns the first two principal components."""

    inputs = {
        "scaled_dataframe": Input(
            description="The scaled dataframe to reduce", type=pd.DataFrame
        ),
    }
    outputs = {
        "pca_components": Output(
            description="The first two principal components", type=pd.DataFrame
        ),
    }

    def process(self, scaled_dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
        pca = PCA(n_components=2)
        pca_components = pd.DataFrame(
            pca.fit_transform(scaled_dataframe), columns=["PC1", "PC2"]
        )
        return {
            "pca_components": pca_components,
        }


class KMeansNClusters(Component):
    """Finds the optimal number of clusters for K-means clustering using silhouette method."""

    inputs = {
        "scaled_dataframe": Input(
            description="The scaled dataframe to cluster", type=pd.DataFrame
        ),
        "max_clusters": Input(
            description="The maximum number of clusters to consider",
            type=int,
            mode=InputMode.STICKY,
        ),
    }
    outputs = {
        "n_clusters": Output(description="The optimal number of clusters", type=int),
    }

    def process(
        self, scaled_dataframe: pd.DataFrame, max_clusters: int
    ) -> dict[str, int]:
        best_score = -1
        best_n_clusters = 0

        for n_clusters in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n_clusters)
            labels = kmeans.fit_predict(scaled_dataframe)
            score = silhouette_score(scaled_dataframe, labels)

            if score > best_score:
                best_score = score
                best_n_clusters = n_clusters

        return {"n_clusters": best_n_clusters}


@dataclass
class KMeansResult:
    """K-means clustering result.

    Attributes:
        clustered_dataframe (pd.DataFrame): The dataframe with cluster labels.
        cluster_labels: The cluster labels.
        centroids: The cluster centroids.
    """

    clustered_dataframe: pd.DataFrame
    cluster_labels: pd.Series
    centroids: pd.DataFrame


class KMeansCluster(Component):
    """Clusters the dataframe using K-means clustering."""

    inputs = {
        "scaled_dataframe": Input(
            description="The scaled dataframe to cluster", type=pd.DataFrame
        ),
        "n_clusters": Input(
            description="The number of clusters", type=int, mode=InputMode.STICKY
        ),
    }
    outputs = {
        "kmeans_result": Output(
            description="K-means clustering result", type=KMeansResult
        ),
    }

    def process(
        self, scaled_dataframe: pd.DataFrame, n_clusters: int
    ) -> dict[str, KMeansResult]:
        kmeans = KMeans(n_clusters=n_clusters)
        labels = kmeans.fit_predict(scaled_dataframe)
        centroids = pd.DataFrame(
            kmeans.cluster_centers_, columns=scaled_dataframe.columns
        )
        clustered_dataframe = scaled_dataframe.copy()
        clustered_dataframe["cluster"] = labels

        # We pack results together so that they are passed as a single message
        result = KMeansResult(
            clustered_dataframe=clustered_dataframe,
            cluster_labels=pd.Series(labels),
            centroids=centroids,
        )

        return {"kmeans_result": result}


class Visualize(Component):
    """Visualizes the clustered dataframe."""

    inputs = {
        "pca_components": Input(
            description="The first two principal components", type=pd.DataFrame
        ),
        "pca_centroids": Input(
            description="The centroids in PCA space", type=pd.DataFrame
        ),
        "kmeans_result": Input(
            description="K-means clustering result", type=KMeansResult
        ),
    }

    def plot(self):
        pca_components = self.pca_components
        pca_centroids = self.pca_centroids
        kmeans_result = self.kmeans_result
        pca_components.plot.scatter(
            x="PC1",
            y="PC2",
            c=kmeans_result.clustered_dataframe["cluster"],  # type: ignore
            cmap="viridis",
        )
        x = pca_components.iloc[:, 0].values
        y = pca_components.iloc[:, 1].values

        plt.scatter(
            x, y, c=kmeans_result.cluster_labels, alpha=0.5, s=200  # type: ignore
        )  # plot different colors per cluster
        plt.title("Wine clusters")
        plt.xlabel("PCA 1")
        plt.ylabel("PCA 2")

        x = pca_centroids.iloc[:, 0].values
        y = pca_centroids.iloc[:, 1].values

        plt.scatter(
            x,  # type: ignore
            y,  # type: ignore
            marker="X",
            s=200,
            linewidths=1.5,
            color="red",
            edgecolors="black",
            label="Centroids",
        )

        plt.show()

    def process(
        self,
        pca_components: pd.DataFrame,
        pca_centroids: pd.DataFrame,
        kmeans_result: KMeansResult,
    ):
        pd.set_option("display.max_rows", 200)
        print("Clustered data:")
        print(kmeans_result.clustered_dataframe)

        print("Cluster centroids:")
        print(kmeans_result.centroids.head(10))

        print("Data in 2d PCA space:")
        print(pca_components.head(10))

        print("Centroids in 2d PCA space:")
        print(pca_centroids.head(10))

        # Here is the trick: we save the data to the instance so that it can be accessed in the plot method.
        # Then we call the plot method from the main thread on component shutdown.
        self.pca_components = pca_components
        self.pca_centroids = pca_centroids
        self.kmeans_result = kmeans_result

    def shutdown(self):
        self.plot()
