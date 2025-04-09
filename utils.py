import plotly.express as px
import plotly.graph_objects as go
import chromadb
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
import os

load_dotenv(override=True)

chroma_client = chromadb.PersistentClient(path="chromadb")

collection_posts = chroma_client.get_collection(name="posts")
collection_comments = chroma_client.get_collection(name="comments")


def plot_sentiment_pie_chart(bullish_count, neutral_count, bearish_count):
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


def plot_stock_sentiment_chart(query_results, stock_name, start_year, end_year):
    # Create a DataFrame from the results
    df_sentiments = pd.DataFrame(query_results)

    # Convert the 'date' column to datetime
    df_sentiments['date'] = pd.to_datetime(df_sentiments['date'])

    # Extract the month from the 'date' column
    df_sentiments['Month'] = df_sentiments['date'].dt.to_period('M')

    # Group by 'Month' and calculate the sum of 'bearish_count', 'bullish_count', and 'neutral_count'
    df_sentiments = df_sentiments.groupby('Month')[['bearish_count', 'bullish_count', 'neutral_count']].sum().reset_index()


    # Normalize the sentiment counts so each row adds up to 1
    df_sentiments[['bearish_count', 'bullish_count']] = df_sentiments[['bearish_count', 'bullish_count']].div(
        df_sentiments[['bearish_count', 'bullish_count']].sum(axis=1), axis=0)

    if not stock_name:
        df_merged = df_sentiments
        df_merged['Close'] = 0
    else:
        df_stockprices = yf.download(stock_name, start=f"{start_year}-01-01", end=f"{end_year+1}-01-01")
        if df_stockprices.empty:
            df_merged = df_sentiments
            df_merged['Close'] = 0
        else:
            df_stockprices.index = pd.to_datetime(df_stockprices.index)
            df_stockprices.columns = df_stockprices.columns.droplevel(1)
            df_stockprices.reset_index(inplace=True)
            df_stockprices['Month'] = df_stockprices['Date'].dt.to_period('M')
            df_stockprices = df_stockprices[['Month', 'Close']]

            df_merged = df_stockprices.merge(df_sentiments, on='Month', how='left')
            df_merged.fillna(0, inplace=True)
        
    df_merged['Month'] = df_merged['Month'].astype(str)
    

    # Calculate the difference between bullish and bearish counts
    df_merged['Bullish-Bearish'] = df_merged['bullish_count'] - df_merged['bearish_count']

    # Create a diverging bar chart using Plotly
    fig = go.Figure()

    # Add bullish bars
    fig.add_trace(go.Bar(
        x=df_merged.loc[df_merged["Bullish-Bearish"] > 0, 'Month'],
        y=df_merged.loc[df_merged["Bullish-Bearish"] > 0, "Bullish-Bearish"] * 3,
        name='Bullish',
        marker_color='green'
    ))

    # Add bearish bars
    fig.add_trace(go.Bar(
        x=df_merged.loc[df_merged["Bullish-Bearish"] < 0, 'Month'],
        y=df_merged.loc[df_merged["Bullish-Bearish"] < 0, "Bullish-Bearish"] * 3,
        name='Bearish',
        marker_color='red'
    ))

    # Overlay stock prices as a line chart
    fig.add_trace(go.Scatter(
        x=df_merged['Month'],
        y=df_merged['Close'],
        name='Stock Price',
        mode='lines',
        line=dict(color='blue')
    ))

    # Update layout for better visualization
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title=f'Stock Price ({stock_name})',
        barmode='relative',
        xaxis_tickangle=45,
        yaxis2=dict(
            title=stock_name,
            overlaying='y',
            side='right'
        )
    )

    return fig


def query_posts(query, top_k=100):
    response = collection_posts.query(
    query_texts=[query], 
    n_results= top_k
    )
    results = response["metadatas"][0]

    for post in results:
        comment_ids = post["comment_ids"].split(",")
        comments = collection_comments.get(comment_ids)["metadatas"]
        post["comments"] = comments

    return results


def sort_posts(post_results, sort_by:str, ascending=False):
    if sort_by not in post_results[0]:
        return False
    
    post_results.sort(key=lambda post: post[sort_by], reverse=not ascending)

    return True

