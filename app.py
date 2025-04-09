import streamlit as st
import utils, os, setup

if not os.path.exists("chromadb"):
    setup.main()


if "results" not in st.session_state:
    st.session_state["results"] = []
    st.session_state["sort_by"] = None
    st.session_state["sort_ascending"] = False

SORT_BY_DICT = {"Relevance":None, "Post Score":"score", "Date Posted":"year"}

st.set_page_config(layout="wide")

st.title("Stock Sentiment Dashboard")
query_container = st.container()
eda_container = st.container(border=True)
results_container = st.container()



with query_container:
    query_col, stock_col, date1_col, date2_col, sort_attribute_col, request_col = st.columns([0.3, 0.2, 0.1, 0.1, 0.2, 0.1])


    with query_col:
        query = st.text_input("Query")

    with stock_col:
        stock_ticker = st.text_input("Stock ticker")

    with date1_col:
        start_year = st.selectbox("Start Year", options=[str(year) for year in range(2013, 2026)])

    with date2_col:
        date_options = [str(year) for year in range(int(start_year), 2026)]
        end_year = st.selectbox("End Year", options=date_options, index=len(date_options)-1)

    with sort_attribute_col:
        sort_by = st.selectbox("Sort by", options=SORT_BY_DICT.keys())

    with request_col:
        st.container(height=12, border=False)
        if st.button(label="Search", type="primary", use_container_width=True):
            print(query, stock_ticker, start_year, end_year)
            results = utils.query_posts(query)
            if SORT_BY_DICT[sort_by]:
                utils.sort_posts(results, sort_by=SORT_BY_DICT[sort_by])
            st.session_state["results"] = results


with eda_container:
    col1, col2 = st.columns([0.66,0.33]) 
    with col1:
        if st.session_state["results"]:
            fig = utils.plot_stock_sentiment_chart(st.session_state["results"], stock_ticker, int(start_year), int(end_year))
            st.plotly_chart(fig, key="stockchart", use_container_width=True)
    with col2:
        sentiment_counts = [0, 0, 0]
        for post in st.session_state["results"]:
            sentiment_counts[0] += post["bullish_count"]
            sentiment_counts[1] += post["neutral_count"]
            sentiment_counts[2] += post["bearish_count"]
        fig = utils.plot_sentiment_pie_chart(sentiment_counts[0], sentiment_counts[1], sentiment_counts[2])
        st.plotly_chart(fig, key="piechart", use_container_width=True)


with results_container:
    if st.session_state["results"]:
        st.subheader(f"Showing {len(st.session_state["results"])} results:")
    for id, post in enumerate(st.session_state["results"]):

        with st.container(border=True):

            st.subheader(f"Title: {post["title"]}")
            st.markdown(f"Date Posted: {post["date"]} | Score: {post["score"]}")
            st.markdown(f"{post["text"]}")




