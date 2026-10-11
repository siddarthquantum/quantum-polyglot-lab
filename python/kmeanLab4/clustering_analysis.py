import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, AgglomerativeClustering
import numpy as np

# 1. Load and prepare the dataset
df = pd.read_csv('CC GENERAL.csv')

# Drop CUST_ID as it is merely an identifier, not a behavioral variable
df = df.drop('CUST_ID', axis=1)

# Handle missing values by filling them with the column mean
df.fillna(df.mean(), inplace=True)

# 2. Task 1: K-Means without scaling (Elbow & Silhouette)
wcss_unscaled = []
silhouette_unscaled = []
K = range(2, 11)

for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(df)
    wcss_unscaled.append(kmeans.inertia_)
    silhouette_unscaled.append(silhouette_score(df, kmeans.labels_))

# 3. Task 2: Standardize the data
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df)

wcss_scaled = []
silhouette_scaled = []

for k in K:
    kmeans_scaled = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans_scaled.fit(df_scaled)
    wcss_scaled.append(kmeans_scaled.inertia_)
    silhouette_scaled.append(silhouette_score(df_scaled, kmeans_scaled.labels_))

# 4. Plotting the results for comparison
fig, ax = plt.subplots(2, 2, figsize=(14, 10))

# Elbow Method plots
ax[0, 0].plot(K, wcss_unscaled, 'bo-')
ax[0, 0].set_title('Elbow Method (Unscaled Data)')
ax[0, 0].set_xlabel('Number of clusters (k)')
ax[0, 0].set_ylabel('WCSS')

ax[0, 1].plot(K, wcss_scaled, 'ro-')
ax[0, 1].set_title('Elbow Method (Scaled Data)')
ax[0, 1].set_xlabel('Number of clusters (k)')
ax[0, 1].set_ylabel('WCSS')

# Silhouette Score plots
ax[1, 0].plot(K, silhouette_unscaled, 'bo-')
ax[1, 0].set_title('Silhouette Score (Unscaled Data)')
ax[1, 0].set_xlabel('Number of clusters (k)')
ax[1, 0].set_ylabel('Score')

ax[1, 1].plot(K, silhouette_scaled, 'ro-')
ax[1, 1].set_title('Silhouette Score (Scaled Data)')
ax[1, 1].set_xlabel('Number of clusters (k)')
ax[1, 1].set_ylabel('Score')

plt.tight_layout()
plt.savefig('clustering_plot.png')

print(f"Max Silhouette Score (Unscaled): {max(silhouette_unscaled):.4f}")
print(f"Max Silhouette Score (Scaled): {max(silhouette_scaled):.4f}")

print("\n--- DBSCAN Outlier Detection ---")
# DBSCAN requires scaled data. eps and min_samples are hyperparameters.
dbscan = DBSCAN(eps=2.0, min_samples=5)
dbscan_labels = dbscan.fit_predict(df_scaled)

# In DBSCAN, outliers/noise are always labeled as -1
outliers_count = list(dbscan_labels).count(-1)
print(f"Number of outliers detected by DBSCAN: {outliers_count}")

# Silhouette score for DBSCAN is only valid if more than 1 cluster is found
if len(set(dbscan_labels)) > 1:
    dbscan_silhouette = silhouette_score(df_scaled, dbscan_labels)
    print(f"DBSCAN Silhouette Score: {dbscan_silhouette:.4f}")
else:
    print("DBSCAN found only 1 cluster or only noise.")

print("\n--- Agglomerative Clustering ---")
# We will use k=4 as a common baseline for this dataset, adjust if your Elbow graph looked different!
optimal_k = 4 
agg_cluster = AgglomerativeClustering(n_clusters=optimal_k)
agg_labels = agg_cluster.fit_predict(df_scaled)
agg_silhouette = silhouette_score(df_scaled, agg_labels)

print(f"Agglomerative Silhouette Score (k={optimal_k}): {agg_silhouette:.4f}")


print("\n--- Agglomerative Clustering ---")
# Take a random sample of 2000 customers to prevent the system from hanging
np.random.seed(42)
sample_indices = np.random.choice(df_scaled.shape[0], size=2000, replace=False)
df_scaled_sample = df_scaled[sample_indices]

optimal_k = 4 
agg_cluster = AgglomerativeClustering(n_clusters=optimal_k)
agg_labels = agg_cluster.fit_predict(df_scaled_sample)
agg_silhouette = silhouette_score(df_scaled_sample, agg_labels)

print(f"Agglomerative Silhouette Score (k={optimal_k}): {agg_silhouette:.4f}")