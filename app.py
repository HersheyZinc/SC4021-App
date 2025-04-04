import streamlit as st
import utils
import random

if "results" not in st.session_state:
    st.session_state["results"] = []
    st.session_state["sort_by"] = None
    st.session_state["sort_ascending"] = False

SORT_BY_DICT = {"None":None, "Post Score":"score", "Comment Count":"num_comments", "Date Posted":"year"}
SORT_ASCENDING_DICT = {"High to Low":False, "Low to High":True}

st.set_page_config(layout="wide")

st.title("Stock Sentiment Searchbar")
query_container = st.container()
results_container = st.container()



with query_container:
    query_col, sort_attribute_col, sort_ascending_col = st.columns([0.6,0.2,0.2])

    with sort_attribute_col:
        sort_by = st.selectbox("Sort by:", list(SORT_BY_DICT.keys()))
        st.session_state["sort_by"] = SORT_BY_DICT[sort_by]


    with sort_ascending_col:
        sort_ascending = st.selectbox("Sort order:", list(SORT_ASCENDING_DICT.keys()))
        st.session_state["sort_ascending"] = SORT_ASCENDING_DICT[sort_ascending]


    with query_col:
        st.container(height=12, border=False)
        if query := st.chat_input("Enter a company or stock name"):
            results = utils.query_posts(query)
            if st.session_state["sort_by"]:
                utils.sort_posts(results, sort_by=st.session_state["sort_by"], ascending=st.session_state["sort_ascending"])
            st.session_state["results"] = results




with results_container:
    for id, post in enumerate(st.session_state["results"]):

        with st.container(border=True):
            col_text, col_stats = st.columns([0.7,0.3])

            with col_text:
                st.markdown(f"Title: {post["title"][0]}")
                st.markdown(f"Year Posted: {post["year"][0]} | Score: {post["score"][0]} | Comments: {post["num_comments"][0]}")
                st.markdown(f"{post["text"][0]}")



            with col_stats:
                # fig = utils.sentiment_pie_chart(post["bullish_count"][0], post["neutral_count"][0], post["bearish_count"][0])
                
                fig = utils.sentiment_pie_chart(random.randint(1, 20), random.randint(0, 20), random.randint(0, 20))
                st.plotly_chart(fig, key=str(id), use_container_width=True)


