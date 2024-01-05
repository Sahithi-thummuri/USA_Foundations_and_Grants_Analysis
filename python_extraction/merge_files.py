import os
import pandas as pd
# load all of the grantees into a dataframe and save to a single csv
dfs = [pd.read_csv(f, dtype={'ein':'string', 'Zip':'string'})
        for f in os.listdir(os.getcwd()) if f.endswith('csv') and f.startswith('grantees')]
finaldf = pd.concat(dfs)
finaldf.to_csv('990pf_grantees.csv', index=False)

# load all of the foundations into a dataframe and save to a single csv
dfs = [pd.read_csv(f, dtype={'ein':'string'})
        for f in os.listdir(os.getcwd()) if f.endswith('csv') and f.startswith('foundations')]

finaldf = pd.concat(dfs)
finaldf.to_csv('990pf_foundations.csv', index=False)


