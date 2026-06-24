# Executive Analytics Dashboard (Retail Sailors ™)

A high-performance, interactive retail analytics dashboard built with **Streamlit** and powered by **DuckDB** as an in-memory SQL backend. This project serves as a portfolio piece demonstrating how to bypass memory-heavy data processing frameworks (like Pandas) in favor of fast, multi-threaded relational logic directly inside a web application lifecycle.

## 🚀 Why DuckDB Over Pandas?

Streamlit reruns the entire Python script on every user interaction (clicks, filters, tab switches). Using traditional Pandas workflows can lead to severe bottlenecks due to:

* **High Memory Overhead:** Copy-pasting, filtering, and chain-merging multiple large DataFrames forces expensive memory allocations.
* **Single-Threaded Execution:** Pandas operations run sequentially, increasing computational lag.

**The Solution:** This dashboard uses an **in-memory DuckDB database** instance cached via Streamlit’s `@st.cache_resource`.

* All raw data partitions (`customers`, `orders`, `products`) are read from local **Parquet** files and structured inside a classic **Star Schema**.
* A singular flattened table (`flat`) is materialized in memory, eliminating slow disk I/O after the initial read.
* Multi-threaded concurrent execution ensures lightning-fast load times, while dynamic `WHERE` clauses handle real-time global filtering natively in SQL.

---

## 🛠️ Tech Stack & Key Libraries

* **Frontend Framework:** Streamlit
* **Database Engine:** DuckDB (In-memory OLAP)
* **Visualizations:** Plotly (Graph Objects, Express, Subplots)
* **UI Components:** Streamlit Option Menu
* **Data Format:** Apache Parquet

---

## 📊 Dashboard Modules

The application is structured into three distinct analytical views accessible via a responsive global navigation menu:

1. **Sales Analysis:** Tracks high-level executive KPIs (Total Sales, Total Profit, Unique Customers, and Profit Margin) alongside historical interactive multi-axis monthly revenue, order volume, and profitability trends.
2. **Product Analysis:** Breaks down product category performance, revenue distribution shares (Pie Charts), and details top 10 / bottom 10 products by overall financial contribution.
3. **Customer Analysis:** Evaluates geographic revenue metrics by country and isolates high-value customer accounts via organized relational tabular views.

---

## 🗂️ Data Architecture

The underlying architecture models a structured retail star schema, transformed into a unified analytical layer for accelerated query execution:

---

## ⚡ Quick Start & Installation

1. Download or clone the repository,
2. Create venv and download the dependency mentioned in `pyproject.toml` or install `uv` package manager `pip install uv` and run comand `uv sync` it will automatically create a venv from `uv.lock` file.
3. after completing setup, run the streamlit app with comand `streamlit run main.py`,  if you are using uv run `uv run streamlit run main.py`
