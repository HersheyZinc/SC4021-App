import streamlit as st
import utils

st.set_page_config(layout="wide")

# --- Session State Initialization (remains the same) ---
if "results" not in st.session_state:
    st.session_state["results"] = []

SORT_BY_DICT = {"Relevance":None, "Post Score":"score", "Date Posted":"year"}
DISPLAY_COUNT = 20

st.title("Stock Sentiment Dashboard")
query_container = st.container()
eda_container = st.container(border=True)
results_container = st.container()

# Container to take user inputs
with query_container:
    query_col, stock_col, date1_col, date2_col, sort_attribute_col, request_col = st.columns([0.3, 0.2, 0.1, 0.1, 0.2, 0.1])

    # Column to get user query
    with query_col:
        query = st.text_input("Query")

    # Column to get stock ticker
    with stock_col:
        stock_ticker = st.text_input("Stock ticker")

    # Column to get start year
    with date1_col:
        start_year = st.selectbox("Start Year", options=[str(year) for year in range(2013, 2026)])

    # Column to get end year
    with date2_col:
        date_options = [str(year) for year in range(int(start_year), 2025)]
        end_year = st.selectbox("End Year", options=date_options, index=len(date_options)-1)

    # Column to get sorting option
    with sort_attribute_col:
        sort_by = st.selectbox("Sort by", options=SORT_BY_DICT.keys())

    # Button to execute retrieval
    with request_col:
        st.container(height=12, border=False)
        if st.button(label="Search", type="primary", use_container_width=True):
            # print(query, stock_ticker, start_year, end_year)
            results = utils.query_posts(query, start_year, end_year)
            st.session_state["results"] = results


# Container to display overall EDA for retrieved posts
with eda_container:
    col1, col2 = st.columns([0.66,0.33]) 
    with col1:
        if st.session_state["results"]:
            fig = utils.plot_stock_sentiment_chart(st.session_state["results"], stock_ticker, int(start_year), int(end_year))
            st.plotly_chart(fig, key="stockchart", use_container_width=True)
    
    with col2:
        fig = utils.plot_sentiment_pie_chart(st.session_state["results"], int(start_year), int(end_year))
        st.plotly_chart(fig, key="piechart", use_container_width=True)


with results_container:
    st.markdown("---")
    results_count = len(st.session_state['results'])
    count = 0
    st.subheader(f"Displaying {min(DISPLAY_COUNT, results_count)} of {results_count} results:")

    for id_num, post in enumerate(st.session_state["results"]):
        count += 1
        if count > DISPLAY_COUNT:
            break
        with st.container(border=True):

            # 1. Title
            st.markdown(f"**Title:** {post["title"]}")
            # 2. Stats Line (Exact Date, Score, Comments Count)
            st.markdown(f"**Posted:** {post["year"]}-{post["month"]}-{post['day']} | **Score:** {post['score']:.0f}")
            # 3. Full Text Content
            st.markdown(f"**Content:**\n{post["text"]}")
            # --- End display ---


