#%%
import pandas as pd
#%%
customers = pd.read_csv(r'dataset\raw_dataset\Customers.csv',delimiter=';')
orders = pd.read_csv(r'dataset\raw_dataset\Orders.csv',delimiter=';')
products = pd.read_csv(r'dataset\raw_dataset\Products.csv',delimiter=';')

#%%
orders.info()

#%%
# formated the order date and shipping date column to date format

orders['Order_Date'] = pd.to_datetime(orders['Order_Date'],format='mixed')
orders['Shipping_Date'] = pd.to_datetime(orders['Shipping_Date'],format='mixed')

#%%
# fixed the european type decimal comma and thousands period system to indian style
orders['Sales']= orders['Sales'].str.replace(',','.',regex=True).astype(float)
orders['Discount']= orders['Discount'].str.replace(',','.',regex=True).astype(float)
orders['Profit']= orders['Profit'].str.replace(',','.',regex=True).astype(float)
orders['Unit_Price']= orders['Unit_Price'].str.replace(',','.',regex=True).astype(float)

#%%
# added essential day and month columns to the orders table
orders['day'] = orders['Order_Date'].dt.day
orders['month'] = orders['Order_Date'].dt.month
orders['year'] = orders['Order_Date'].dt.year
orders['day_of_week'] = orders['Order_Date'].dt.day_of_week
orders['year_month'] = orders['Order_Date'].dt.strftime('%Y-%m')
orders['Days_to_Ship'] = (orders['Shipping_Date'] - orders['Order_Date']).dt.days
#%%
orders.head(1)

#%%
customers['Country'].nunique()
#%%
# converted Id columns to string
orders['Customer_ID'] = orders['Customer_ID'].astype(str)
customers['Customer_ID'] = customers['Customer_ID'].astype(str)
orders['Product_ID'] = orders['Product_ID'].astype(str)
products['Product_ID'] = products['Product_ID'].astype(str)
#%%
# cleaned the dimension columns to remove any trailing spaces
customers['City'] = customers['City'].str.strip().str.title()
customers['Country'] = customers['Country'].str.strip().str.title()
products['Category'] = products['Category'].str.strip()
products['Sub_Category'] = products['Sub_Category'].str.strip()
#%%
products
#%% [markdown]
### there is no further need of cleaning the dataset as all the values are non null. and formated standardly
### thus store it in seperate directory in dataset directory
### using parquet format cause its storage efficient and loads faster than csv.
# %%
orders.to_parquet(r'dataset\cleaned_dataset\orders.parquet')
customers.to_parquet(r'dataset\cleaned_dataset\customers.parquet')
products.to_parquet(r'dataset\cleaned_dataset\products.parquet')

