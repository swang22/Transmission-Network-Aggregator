import pandas as pd
import numpy as np

df = pd.read_csv('county_edges_tx.csv')
cap = df['Tx_Capacity_MW']

print('Capacity statistics:')
print(f'Min: {cap.min():.0f} MW')
print(f'Max: {cap.max():.0f} MW')
print(f'Mean: {cap.mean():.0f} MW')
print(f'Median: {cap.median():.0f} MW')

print('\nPercentiles:')
for p in [10, 25, 50, 75, 90, 95, 99]:
    print(f'{p}th: {np.percentile(cap, p):.0f} MW')

print('\nCapacity distribution:')
bins = [0, 200, 500, 1000, 2000, 5000, float('inf')]
labels = ['<200', '200-500', '500-1K', '1K-2K', '2K-5K', '5K+']
df['cap_class'] = pd.cut(cap, bins=bins, labels=labels, right=False)
print(df['cap_class'].value_counts().sort_index())
