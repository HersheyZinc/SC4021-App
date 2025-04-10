import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import pysolr, os
from dotenv import load_dotenv
import streamlit as st

load_dotenv(override=True)

SOLR_ADDRESS = os.getenv('SOLR_ADDRESS')
if not SOLR_ADDRESS:
    raise EnvironmentError("FATAL ERROR: SOLR_ADDRESS environment variable not set. Please configure .env file.")
try:
    SOLR = pysolr.Solr(SOLR_ADDRESS, timeout=10)
    SOLR.ping()
except Exception as e:
    raise ConnectionError(f"FATAL ERROR: Could not connect to Solr at {SOLR_ADDRESS}. Error: {e}")



def plot_sentiment_pie_chart(query_results, start_year, end_year):
    '''
    Displays sentiment counts as a pie chart
    '''
    if len(query_results) == 0:
        values, labels, colors = [1], ["No sentiments"], ["gray"]
    else:
        df_sentiments = pd.DataFrame(query_results)

        # Filter the DataFrame to include only rows within the specified time frame
        df_filtered = df_sentiments[(df_sentiments['year'] >= start_year) & (df_sentiments['year'] <= end_year)]

        # Calculate total sentiment counts within the time frame
        bullish_count = df_filtered['bullish_count'].sum()
        neutral_count = df_filtered['neutral_count'].sum()
        bearish_count = df_filtered['bearish_count'].sum()

        # Prepare data for the pie chart
        values = [bullish_count, neutral_count, bearish_count]
        labels = ['Bullish', 'Neutral', 'Bearish']
        colors = ['green', 'gray', 'red']

    # Create the pie chart using Plotly
    fig = px.pie(values=values, names=labels, color_discrete_sequence=colors,)

    return fig


def plot_stock_sentiment_chart(query_results, stock_name, start_year, end_year):
    '''
    Function to overlay stock sentiments over stock price.
    '''
    # Create a DataFrame from the results
    df_sentiments = pd.DataFrame(query_results)

    df_sentiments['Year-Month'] = df_sentiments['year'].astype(str) + '-' + df_sentiments['month'].astype(str).str.zfill(2)

    # Group by 'Year-Month' and calculate the sum of sentiments in each month
    df_sentiments = df_sentiments.groupby('Year-Month')[['bearish_count', 'bullish_count', 'neutral_count']].sum().reset_index()

    # Normalize the sentiment counts so each row adds up to 1
    df_sentiments[['bearish_count', 'bullish_count']] = df_sentiments[['bearish_count', 'bullish_count']].div(
    df_sentiments[['bearish_count', 'bullish_count']].sum(axis=1), axis=0)
    df_sentiments['Bullish-Bearish'] = df_sentiments['bullish_count'] - df_sentiments['bearish_count']

    # Handle historical stock data
    if not stock_name:
        df_merged = df_sentiments
        df_merged['Close'] = 0
    else:
        # Download historical stock data from Yahoo Finance
        df_stockprices = yf.download(stock_name, start=f"{start_year}-01-01", end=f"{end_year+1}-01-01")
        if df_stockprices.empty:
            df_merged = df_sentiments
            df_merged['Close'] = 0
        else:
            # Format data by month and get the monthly Close price of the stock
            df_stockprices.index = pd.to_datetime(df_stockprices.index)
            df_stockprices.columns = df_stockprices.columns.droplevel(1)
            df_stockprices.reset_index(inplace=True)
            df_stockprices['Year-Month'] = df_stockprices['Date'].dt.to_period('M').astype(str)
            df_stockprices = df_stockprices[['Year-Month', 'Close']]

            df_merged = df_stockprices.merge(df_sentiments, on='Year-Month', how='left')
            df_merged.fillna(0, inplace=True)
        

    # Create a diverging bar chart using Plotly
    fig = go.Figure()

    # Add bullish bars
    fig.add_trace(go.Bar(
        x=df_merged.loc[df_merged["Bullish-Bearish"] > 0, 'Year-Month'],
        y=df_merged.loc[df_merged["Bullish-Bearish"] > 0, "Bullish-Bearish"] * 3,
        name='Bullish',
        marker_color='green'
    ))

    # Add bearish bars
    fig.add_trace(go.Bar(
        x=df_merged.loc[df_merged["Bullish-Bearish"] < 0, 'Year-Month'],
        y=df_merged.loc[df_merged["Bullish-Bearish"] < 0, "Bullish-Bearish"] * 3,
        name='Bearish',
        marker_color='red'
    ))

    # Overlay stock prices as a line chart
    fig.add_trace(go.Scatter(
        x=df_merged['Year-Month'],
        y=df_merged['Close'],
        name='Stock Price',
        mode='lines',
        line=dict(color='blue')
    ))

    # Update layout for better visualization
    fig.update_layout(
        xaxis_title='Year-Month',
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



def query_posts(query:str, start_date:str=None, end_date:str=None, sort=None, top_k:int=10000):
    q = f"title:{query} OR text:{query}"
    from datetime import datetime, time


    filters = []
    # Convert start_date and end_date from year to '%Y-%m-%dT%H:%M:%SZ' format
    if start_date and end_date:
        solr_start_date = f"{start_date}-01-01T00:00:00Z"
        solr_end_date = f"{end_date}-12-31T23:59:59Z"

        filters.append(f"date:[{solr_start_date} TO {solr_end_date}]")
    

    # Execute the search
    results = SOLR.search(q, rows=top_k, fq=filters)



    for result in results:
        for key in result.keys():
            if key not in ("comment_texts", "comment_sentiments", "comment_scores", "tickers"):
                if isinstance(result[key], list) and len(result[key]) == 1:
                    result[key] = result[key][0]

    return results