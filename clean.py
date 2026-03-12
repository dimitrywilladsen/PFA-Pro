import pandas as pd
import os

filename = 'fitness_log.csv'

if os.path.exists(filename):
    print("⚓ Admiral on Deck: Starting data purge...")
    df = pd.read_csv(filename)
    initial_count = len(df)
    
    # 1. Strip whitespace from columns just in case
    df.columns = df.columns.str.strip()
    
    # 2. Keep EVERYTHING that isn't a 'Passive' log
    others = df[df['type'] != 'Passive']
    
    # 3. For 'Passive' logs, only keep ONE per unique date
    passives = df[df['type'] == 'Passive']
    clean_passives = passives.drop_duplicates(subset=['date'], keep='first')
    
    # 4. Recombine
    final_df = pd.concat([others, clean_passives], ignore_index=True)
    
    # 5. Save back to CSV
    final_df.to_csv(filename, index=False)
    
    print(f"✅ Mission Success!")
    print(f"Removed {initial_count - len(final_df)} duplicate entries.")
    print(f"Remaining entries: {len(final_df)}")
else:
    print("❌ Error: fitness_log.csv not found in this folder.")