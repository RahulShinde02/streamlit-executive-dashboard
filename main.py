import streamlit as st
import duckdb
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# for this project i am choosing DuckDB for data filtering over Pandas to power
# our Streamlit backend for better scalability.
# Because Streamlit reruns the script on every user interaction, DuckDB's multi-threaded,
# concurrent execution model ensures lightning-fast load times. Additionally, writing relational
# logic in native SQL avoids the massive memory overhead and computational lag associated with
# chain-merging multiple Pandas DataFrames.


# our dataset is small so in memory database will be fine to handle filtering queries faster,
# eleminating the slow disk reading IO operations entirely after initial reads.
# and we will be using streamlit cache so it wont be a problem if user adds filters

# ======================================================================================================================
#                                                Data Caching
# ======================================================================================================================


@st.cache_resource
def db_init():
    """creating in-mempry database, adding the dataset and caching it in streamlit cache, and returning the connection"""
    con = duckdb.connect(database=":memory:")
    con.execute(
        "CREATE TABLE customer AS SELECT * FROM 'dataset/cleaned_dataset/customers.parquet'"
    )
    con.execute(
        "CREATE TABLE orders AS SELECT * FROM 'dataset/cleaned_dataset/orders.parquet'"
    )
    con.execute(
        "CREATE TABLE products AS SELECT * FROM 'dataset/cleaned_dataset/products.parquet'"
    )
    # our data structure is star schema and data size is very low so insted of creating a view ,
    # we can create a new table with all data
    query = "create or replace table flat as select * from orders o left join customer c on c.Customer_ID = o.Customer_ID left join products p on o.Product_ID = p.Product_ID"
    con.execute(query)
    return con


# lets cache the files which will be used like logo png
# so it will not read from disk again on refresh/ user interactions
@st.cache_data
def get_Data(path: str):
    with open(path, "rb") as f:
        return f.read()


# =========================================================================================================================
#                                                  Option Menu
# =========================================================================================================================

# here we are setting option menu for different sections of dashboard so whole dashboard will not load at once,
#  it will be fast, look clean and organized
selected_dashboard = option_menu(
    menu_title=None,
    options=["Sales Analysis", "Product Analysis", "Regional Analysis"],
    icons=["graph-up-arrow", "box-seam", "globe"],
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0px",
            "background-color": "#f0f2f6",
            "border-radius": "8px",
        },
        "icon": {"color": "#4A90E2", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "padding": "10px 0px",
            "color": "black",
        },
        "nav-link-selected": {
            "background-color": "#FFDD00",
            "color": "white",
            "font-weight": "600",
        },
    },
)

st.set_page_config(page_title="Executive Analytics Dashboard", layout="wide")

# logo in sidebar so it wont take valuable space on main dashboard
st.sidebar.image(get_Data("dataset/images/logo.jpg"))
st.sidebar.title("Retail Sailors ™", text_alignment="center")
#########################################################################################################################
#                                             Sidebar and filter section
##########################################################################################################################

# lets use cursor object so multiple users will get their seperate thread
con = db_init()
cursor = con.cursor()

# getting the values for filters from database
start_date = cursor.execute("SELECT MIN(Order_Date) FROM flat").fetchone()[0]
end_date = cursor.execute("SELECT MAX(Order_Date) FROM flat").fetchone()[0]
countries_list = (
    cursor.execute("select distinct Country from flat").df()["Country"].tolist()
)
category_list = (
    cursor.execute("select distinct Category from flat").df()["Category"].tolist()
)

st.sidebar.markdown("---")
st.sidebar.header("Global Filters")

# creaiing multiselection filters for dashboard
date_range = st.sidebar.date_input(
    "Select Date Range", [], min_value=start_date, max_value=end_date
)
st.sidebar.text(
    f"📅 Data Available From : \n{start_date.strftime('%Y-%m-%d')}  to  {end_date.strftime('%Y-%m-%d')}"
)
selected_country = st.sidebar.multiselect(
    "Countries :", countries_list, default=countries_list, key="select_count_key"
)
selected_categories = st.sidebar.multiselect(
    "Product Category :",
    category_list,
    default=category_list,
    key="select_category_key",
)


# defining a where clause building function so we will not need to write where clause in sql again and again
def where_builder(**kwargs):
    date_range = kwargs.get("date_range")
    selected_categories = kwargs.get("selected_categories")
    selected_country = kwargs.get("selected_country")
    clauses = ["1=1"]
    if len(date_range) == 2:
        start_date, end_date = date_range
        year_str = f"Order_Date >= '{start_date}' and Order_Date <= '{end_date}'"
        clauses.append(year_str)
    if selected_categories:
        category_str = ",".join(f"'{c}'" for c in selected_categories)
        clauses.append(f"Category in ({category_str})")
    if selected_country:
        country_str = ",".join(f"'{c}'" for c in selected_country)
        clauses.append(f"Country in ({country_str})")
    return " and ".join(clauses)


######################################################################################################################################
#                                                  Sales Analytics Section
######################################################################################################################################

if selected_dashboard == "Sales Analysis":
    where_clause = where_builder(
        date_range=date_range,
        selected_categories=selected_categories,
        selected_country=selected_country,
    )
    # here ↑ we will accept everything from global
    st.title("KPI")
    # KPI cards for total sale, total profit,total customers,profit margins
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            query = f"SELECT ROUND(SUM(Sales)) FROM flat WHERE {where_clause}"
            total_sales = cursor.execute(query).fetchone()[0]
            st.metric(
                label="Total Sales",
                value=f"$ {total_sales:,.0f}",
            )
        except Exception:
            st.text("No data found for this selection.")

    with col2:
        try:
            query = f"SELECT ROUND(SUM(profit)) FROM flat WHERE {where_clause}"
            total_profit = cursor.execute(query).fetchone()[0]
            st.metric(label="Profit", value=f"$ {total_profit:,.0f}")
        except Exception:
            st.text("No data found for this selection.")

    with col3:
        try:
            query = f"SELECT COUNT(DISTINCT Customer_ID) FROM flat where {where_clause}"
            total_customers = cursor.execute(query).fetchone()[0]
            st.metric(label="Customers", value=f"{total_customers:,.0f}")
        except Exception:
            st.text("No data found for this selection.")
        
    with col4:
        try:
            profit_mg = total_profit / total_sales
            st.metric(label="Profit Margin", value=f"{profit_mg:.1%}")
        except Exception:
            st.text("No data found for this selection.")

    # dual axis bar graph for sales and order count
    try:
        query = f"select year_month, sum(sales) as sales , count(Order_ID) as orders, from flat WHERE  {where_clause} group by year_month order by year_month asc;"
        monthly_rev_cust = cursor.execute(query).df()

        st.header("Revenue and Order Trends")
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=monthly_rev_cust["year_month"],
                y=monthly_rev_cust["sales"],
                name="Revenue",
                marker_color="#21a3f1",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=monthly_rev_cust["year_month"],
                y=monthly_rev_cust["orders"],
                mode="lines+markers",
                name="Orders",
                line=dict(color="orange", width=3),
            ),
            secondary_y=True,
        )

        fig.update_layout(
            xaxis_title="Months", yaxis=dict(title="Revenue"), yaxis2=dict(title="Orders")
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")

    # bar chart showing month wise profit
    try:
        query = f"select year_month as Month, sum(profit) as Profit from flat WHERE  {where_clause} group by year_month order by year_month asc;"
        monthly_profit = cursor.execute(query).df()
        st.header("Monthly Profit Trends")

        fig = go.Figure()
        bar_colors = ["red" if val < 0 else "#21a3f1" for val in monthly_profit["Profit"]]
        fig.add_trace(
            go.Bar(
                x=monthly_profit["Month"],
                y=monthly_profit["Profit"],
                marker_color=bar_colors,
                name="Profit",
            )
        )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Profit",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")
    query = f"Select * from flat where {where_clause}"


###########################################################################################################################
#                                                   Product Section
###########################################################################################################################

if selected_dashboard == "Product Analysis":
    # we will use only country and date here
    where_clause = where_builder(
        date_range=date_range, selected_country=selected_country
    )
    st.title("Category Performance")

    # cards for product categories
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            query = f"select sum(sales) from flat where category = 'Office Supplies' and {where_clause};"
            os_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="Office Supplies Revenue", value=f"${os_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")  

    with col2:
        try:
            query = f"select sum(sales) from flat where category = 'Technology'and {where_clause};"
            tec_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="Tech-Product Revenue", value=f"${tec_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")

    with col3:
        try:
            query = f"select sum(sales) from flat where category = 'Furniture'and {where_clause};"
            fu_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="Furniture - Revenue", value=f"${fu_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")

    # pie chart showing each product category share in revenue
    try:
        query = f"select Category, sum(sales) as rev from flat where {where_clause} group by Category"
        pro_cat_rev = cursor.execute(query).df()
        fig = px.pie(pro_cat_rev, names="Category", values="rev")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")

    # top and bottom 10 products by revenue
    where_clause2 = where_builder(
        date_range=date_range,
        selected_categories=selected_categories,
        selected_country=selected_country,
    )
    try:
        query = f"select Product_Name, sum(sales) as rev from flat where {where_clause2} group by Product_Name order by rev desc limit 20 ;"
        top_20 = cursor.execute(query).df()
        st.header("Top 10 Product by Revenue")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=top_20["rev"],
                y=top_20["Product_Name"],
                orientation="h",
                marker_color="#15dd83",
                name="Top 20 Products",
            )
        )
        fig.update_layout(
            xaxis_title="Revenue",
            yaxis_title="Product Name",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")

    try:
        query = f"select Product_Name, sum(sales) as rev from flat where {where_clause2} group by Product_Name order by rev asc limit 20 ;"
        bottom_20 = cursor.execute(query).df()
        st.header("Bottom 10 Product by Revenue")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=bottom_20["rev"],
                y=bottom_20["Product_Name"],
                orientation="h",
                marker_color="#cc2d2d",
                name="Bottom 20 Products",
            )
        )
        fig.update_layout(
            xaxis_title="Revenue",
            yaxis_title="Product Name",
            yaxis=dict(
                categoryorder="array", categoryarray=bottom_20["Product_Name"][::-1]
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")
    # --------------------------------------------------------------------------------------------------------------------------
    # top and bottom 10 generiting profit/loss
    try:
        query = f"select Product_Name, sum(profit) as rev from flat where {where_clause2} group by Product_Name order by rev desc limit 20 ;"
        top_20_p = cursor.execute(query).df()
        st.header("Top 10 Profit-Generating Products")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=top_20_p["rev"],
                y=top_20_p["Product_Name"],
                orientation="h",
                marker_color="#0dff00",
                name="Top 20 Products",
            )
        )
        fig.update_layout(
            xaxis_title="Profit",
            yaxis_title="Product Name",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")

    try:    
        query = f"select Product_Name, sum(profit) as rev from flat where {where_clause2} group by Product_Name order by rev asc limit 20 ;"
        bottom_20_p = cursor.execute(query).df()
        st.header("10 Lowest Performing Products")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=bottom_20_p["rev"],
                y=bottom_20_p["Product_Name"],
                orientation="h",
                marker_color="#ff0000",
                name="Bottom 20 Products",
            )
        )
        fig.update_layout(
            xaxis_title="Profit/Loss",
            yaxis_title="Product Name",
            yaxis=dict(
                categoryorder="array", categoryarray=bottom_20["Product_Name"][::-1]
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")
###########################################################################################################################
#                                                customer Section
###########################################################################################################################

if selected_dashboard == "Regional Analysis":
    where_clause = where_builder(
        date_range=date_range, selected_categories=selected_categories
    )
    where_clause2 = where_builder(
        date_range=date_range, selected_country=selected_country
    )
    st.title("Country wise Revenue")
    # cards showing revenue of countries.
    # we have to hardcode it, it can be made dynamic with Globals injection but our script/app should be predictable
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        try:
            query = (
                f"select sum(sales) from flat where Country = 'France' and {where_clause} "
            )
            france_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="France", value=f"${france_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")
    with col2:
        try:
            query = (
                f"select sum(sales) from flat where Country = 'Germany' and {where_clause} "
            )
            Germany_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="Germany", value=f"${Germany_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")
    with col3:
        try:
            query = f"select sum(sales) from flat where Country = 'Usa' and {where_clause} "
            usa_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="USA", value=f"${usa_rev:,.0f}")
        except Exception:
            st.text("No data found for this selection.")
    with col4:
        try:
            query = (
                f"select sum(sales) from flat where Country = 'Italy' and {where_clause} "
            )
            itlly_rev = cursor.execute(query).fetchone()[0]
            st.metric(label="Italy", value=f"${itlly_rev:,.0f}")
        except Exception:
            st.text("no data available fot this filter")

    # pie chart shoeing countrywise contribution iin revenue
    try:
        query = f"select upper(Country) as Country, sum(sales) as Revenue from flat where {where_clause} group by Country;"
        country_rev = cursor.execute(query).df()
        fig = px.pie(country_rev, names="Country", values="Revenue")
        st.header("Revenue Share by Country")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")

    # top 20 customers contributing in revenue
    try:
        query = f"select Customer_ID, CONCAT(First_Name, ' ', Last_Name) AS Name, Country, round(sum(sales),2) as Revenue from flat where {where_clause2} group by Customer_ID , Name, Country order by Revenue desc limit 20"
        top_20_cust = cursor.execute(query).df()
        st.header("Top 20 Customers by Revenue")
        st.dataframe(top_20_cust,use_container_width=True)
    except Exception:
        st.text("No data found for this selection.")