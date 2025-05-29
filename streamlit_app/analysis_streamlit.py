import streamlit as st
import pandas as pd
from analysis_agent import AnalysisAgent

agent = AnalysisAgent()
st.set_page_config(layout="wide")

st.title("Financial Analysis Agent")

st.sidebar.header("Analysis Options")
analysis_type = st.sidebar.selectbox("Choose Analysis Type", [
    "Investment by Region/Sector", 
    "Portfolio Value Change", 
    "Sentiment Trends",
    "Stock Price Comparison"
])

if analysis_type == "Investment by Region/Sector":
    st.header("Investment by Region and Sector")
    col1, col2, col3 = st.columns(3)
    with col1:
        region = st.text_input("Region (e.g., Asia, US)", "Asia")
    with col2:
        sector = st.text_input("Sector (e.g., Tech, Auto)", "Tech")
    with col3:
        data_type = st.selectbox("Data (Today/Yesterday)", ['today', 'yesterday'], index=0)
    
    if st.button("Calculate Investment"):
        try:
            total_investment = agent.get_investment_by_region_sector(region, sector, data_type)
            st.success(f"Total investment in {region.upper()} {sector.upper()} ({data_type.capitalize()}): ${total_investment:,.2f}")
        except ValueError as e:
            st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

elif analysis_type == "Portfolio Value Change":
    st.header("Portfolio Value Change (Yesterday vs. Today)")
    if st.button("Calculate Portfolio Change"):
        try:
            change_data = agent.get_portfolio_value_change()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Yesterday's Total Value", f"${change_data['yesterday_value']:,.2f}")
            with col2:
                st.metric("Today's Total Value", f"${change_data['today_value']:,.2f}")
            
            st.metric("Absolute Change", f"${change_data['change']:,.2f}", 
                        delta=f"{change_data['percentage_change']:.2f}%")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

elif analysis_type == "Sentiment Trends":
    st.header("Sentiment Analysis of Text")
    default_headlines = "\n".join(agent.news_headlines)
    custom_texts_input = st.text_area("Enter texts to analyze (one per line), or leave blank for default headlines:", 
                                      height=150, value=default_headlines)
    
    if st.button("Analyze Sentiment"):
        try:
            texts_to_analyze = [line.strip() for line in custom_texts_input.split('\n') if line.strip()] 
            if not texts_to_analyze:
                 texts_to_analyze = None # Use default headlines
            
            sentiments_df = agent.get_sentiment_trends(texts=texts_to_analyze)
            st.subheader("Sentiment Scores")
            st.dataframe(sentiments_df, use_container_width=True)
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

elif analysis_type == "Stock Price Comparison":
    st.header("Compare Stock Prices (Yesterday vs. Today)")
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, NVDA-AS)", "AAPL").upper()
    
    if st.button(f"Compare Prices for {ticker}"):
        try:
            price_data = agent.compare_stock_prices(ticker)
            if "error" in price_data:
                st.error(f"Error: {price_data['error']}")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"{price_data['ticker']} - Yesterday's Price", f"${price_data['yesterday_price']:,.2f}")
                with col2:
                    st.metric(f"{price_data['ticker']} - Today's Price", f"${price_data['today_price']:,.2f}")
                
                st.metric("Price Change", f"${price_data['price_change']:,.2f}", 
                            delta=f"{price_data['percentage_price_change']:.2f}%")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Note:** Data is currently using placeholders. In a real system, it would be fetched from other agents or live sources.") 