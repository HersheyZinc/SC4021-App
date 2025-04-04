import plotly.express as px
import pysolr
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os

load_dotenv(override=True)

SOLR_ADDRESS = os.getenv('SOLR_ADDRESS')
SOLR = pysolr.Solr(SOLR_ADDRESS, timeout=10)


def sentiment_pie_chart(bullish_count, neutral_count, bearish_count):
    values = []
    labels = []
    colors = []

    if bullish_count:
        values.append(bullish_count)
        colors.append("green")
        labels.append("bullish")

    if neutral_count:
        values.append(neutral_count)
        colors.append("gray")
        labels.append("neutral")

    if bearish_count:
        values.append(bearish_count)
        colors.append("red")
        labels.append("bearish")

    if not values:
        values, labels, colors = [1], ["No sentiments"], ["gray"]

    fig = px.pie(values=values, names=labels, color_discrete_sequence=colors)

    return fig





def get_comments(post):
    post_id = post["id"]
    comment_query = f"document_type:comment AND parent_id:{post_id}"
    comment_results = SOLR.search(comment_query, rows=100)

    post["comments"] = list(comment_results)
    post["num_comments"] = [len(comment_results)]


def query_posts(query, top_k=100):
    post_query = f"document_type:post AND (title:{query} OR text:{query})"
    post_results = SOLR.search(post_query, rows=top_k)
    post_results = list(post_results)


    with ThreadPoolExecutor() as executor:
        executor.map(get_comments, post_results)

    return post_results


def sort_posts(post_results, sort_by:str, ascending=False):
    if sort_by not in post_results[0]:
        return False
    
    post_results.sort(key=lambda post: post[sort_by][0], reverse=not ascending)

    return True