#%% 
import pandas as pd
#%%
orders = pd.read_parquet(r'dataset\cleaned_dataset\orders.parquet')
products = pd.read_parquet(r'dataset\cleaned_dataset\products.parquet')
customers = pd.read_parquet(r'dataset\cleaned_dataset\customers.parquet')
#%%
orders.info()
# %%
products.info()
#%%
customers.info()
#%% [markdown]
## data is all ok to work with