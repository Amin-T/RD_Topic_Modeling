# -*- coding: utf-8 -*-

# Import liberaries and functions
import pandas as pd
import numpy as np
import pickle
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# --- Load pre-processed data ---
print("Loading pre-processed data ...")
treated_pairs = pd.read_pickle("Data/treated_pairs.pkl")
initial_control_pairs = pd.read_pickle("Data/initial_control_pairs.pkl")
with open("Data/knn_dict.pkl", "rb") as f:
    knn_dict = pickle.load(f)

# Preprocessing: group control pairs by year
control_pool_by_year = {
    year: group[['CIK', 'CIK_pair']].to_records(index=False).tolist()
    for year, group in initial_control_pairs.groupby('ryear')
}

# Convert treated_pairs to list of namedtuples (to avoid pandas object serialization)
rows = treated_pairs.to_records(index=False)

# --- Worker function ---
def process_treated_pair(row):
    A, B, T = row.CIK, row.CIK_pair, row.eventX
    year = max(T - 1, 2006)

    A_neighbors = knn_dict.get((A, year), [])
    if not A_neighbors and T>2006:
        A_neighbors = knn_dict.get((A, year+1), [])

    B_neighbors = knn_dict.get((B, year), [])
    if not B_neighbors and T>2006:
        B_neighbors = knn_dict.get((B, year+1), [])

    if not A_neighbors or not B_neighbors:
        return []  # Skip this treated pair
    
    control_pool = control_pool_by_year.get(year, [])
    control_pool_set = set(control_pool + [(b, a) for (a, b) in control_pool])  # bidirectional
    
    result = []
    for A_prime, B_prime in ((a, b) for a in A_neighbors for b in B_neighbors):
        if (A_prime, B_prime) in control_pool_set:
            result.append({
                'treated_pair': (A, B),
                'control_pair': (A_prime, B_prime),
                'match_year': year
            })
    return result

# --- Parallel execution ---
print(f"Starting multiprocessing ({len(rows)} treated pairs) ...")

batchs = np.array_split(rows, 100)

results = []

# if __name__ == "__main__":
for batch in tqdm(batchs):
    with Pool(processes=cpu_count()) as pool:
        output = pool.map(process_treated_pair, batch)
    pool.join()
    results.extend(output)

# Flatten results
valid_control_pairs = [item for sublist in results for item in sublist]

# Save output
with open("valid_control_pairs.pkl", "wb") as f:
    pickle.dump(valid_control_pairs, f)

print(f"Saved {len(valid_control_pairs)} valid control pairs.")
