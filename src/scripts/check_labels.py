import pandas as pd
import os

# Get project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(project_root, 'data/articles_labeled.csv'))
print('Label value ranges:')
for col in ['political_affiliation', 'clickbait', 'sensationalism', 'title_vs_body', 'sentiment', 'toxicity']:
    unique_vals = sorted(df[col].dropna().unique())
    print(f'{col}: {unique_vals} (min={df[col].min()}, max={df[col].max()})')
