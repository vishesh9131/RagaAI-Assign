import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from market_agent import MarketDataAgent
import json

class MarketDataStreamlit:
    def __init__(self):
        self.agent = MarketDataAgent()
    
    def run(self):
        st.set_page_config(
            page_title="Market Data Dashboard",
            page_icon="📈",
            layout="wide"
        )
        
        st.title("📈 Market Data Dashboard")
        st.sidebar.title("Navigation")
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Choose a page",
            ["Stock Price", "Multiple Stocks", "Company Info", "Earnings", "Stock Search"]
        )
        
        if page == "Stock Price":
            self.stock_price_page()
        elif page == "Multiple Stocks":
            self.multiple_stocks_page()
        elif page == "Company Info":
            self.company_info_page()
        elif page == "Earnings":
            self.earnings_page()
        elif page == "Stock Search":
            self.search_page()
    
    def stock_price_page(self):
        st.header("Stock Price Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.text_input("Enter Stock Symbol", value="AAPL", help="e.g., AAPL, GOOGL, MSFT")
        
        with col2:
            period = st.selectbox(
                "Time Period",
                ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
                index=2
            )
        
        if st.button("Get Stock Data", type="primary"):
            with st.spinner("Fetching stock data..."):
                data = self.agent.get_stock_price(symbol.upper(), period)
            
            if "error" in data:
                st.error(data["error"])
            else:
                # Display current price and metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="Current Price",
                        value=f"${data['current_price']}",
                        delta=f"{data['change']} ({data['change_percent']:.2f}%)"
                    )
                
                with col2:
                    st.metric(label="Volume", value=f"{data['volume']:,}")
                
                with col3:
                    st.metric(label="52W High", value=f"${data['high_52w']}")
                
                with col4:
                    st.metric(label="52W Low", value=f"${data['low_52w']}")
                
                # Historical price chart
                if data['historical_data']:
                    df = pd.DataFrame(data['historical_data'])
                    df['Date'] = pd.to_datetime(df.index) if 'Date' not in df.columns else pd.to_datetime(df['Date'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=df['Close'],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"{data['company_name']} ({symbol.upper()}) Stock Price",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Additional info
                st.subheader("Additional Information")
                info_cols = st.columns(3)
                
                with info_cols[0]:
                    st.write(f"**Company:** {data['company_name']}")
                    st.write(f"**Market Cap:** {data['market_cap']}")
                
                with info_cols[1]:
                    st.write(f"**P/E Ratio:** {data['pe_ratio']}")
                    st.write(f"**Previous Close:** ${data['previous_close']}")
    
    def multiple_stocks_page(self):
        st.header("Multiple Stocks Comparison")
        
        symbols_input = st.text_input(
            "Enter Stock Symbols (comma-separated)",
            value="AAPL,GOOGL,MSFT,TSLA",
            help="e.g., AAPL,GOOGL,MSFT"
        )
        
        if st.button("Get Multiple Stocks Data", type="primary"):
            symbols = [s.strip().upper() for s in symbols_input.split(",")]
            
            with st.spinner("Fetching data for multiple stocks..."):
                data = self.agent.get_multiple_stocks(symbols)
            
            # Create comparison table
            comparison_data = []
            for symbol, stock_data in data.items():
                if "error" not in stock_data:
                    comparison_data.append({
                        "Symbol": symbol,
                        "Company": stock_data['company_name'],
                        "Price": stock_data['current_price'],
                        "Change": stock_data['change'],
                        "Change %": stock_data['change_percent'],
                        "Volume": stock_data['volume'],
                        "Market Cap": stock_data['market_cap']
                    })
            
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                
                # Style the dataframe
                styled_df = df.style.format({
                    'Price': '${:.2f}',
                    'Change': '${:.2f}',
                    'Change %': '{:.2f}%',
                    'Volume': '{:,}'
                }).applymap(
                    lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                    subset=['Change', 'Change %']
                )
                
                st.dataframe(styled_df, use_container_width=True)
                
                # Price comparison chart
                price_data = []
                for symbol, stock_data in data.items():
                    if "error" not in stock_data and stock_data['historical_data']:
                        hist_df = pd.DataFrame(stock_data['historical_data'])
                        hist_df['Symbol'] = symbol
                        hist_df['Date'] = pd.to_datetime(hist_df.index)
                        price_data.append(hist_df[['Date', 'Close', 'Symbol']])
                
                if price_data:
                    combined_df = pd.concat(price_data, ignore_index=True)
                    
                    fig = px.line(
                        combined_df,
                        x='Date',
                        y='Close',
                        color='Symbol',
                        title="Stock Price Comparison"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    def company_info_page(self):
        st.header("Company Information")
        
        symbol = st.text_input("Enter Stock Symbol", value="AAPL")
        
        if st.button("Get Company Info", type="primary"):
            with st.spinner("Fetching company information..."):
                data = self.agent.get_company_info(symbol.upper())
            
            if "error" in data:
                st.error(data["error"])
            else:
                st.subheader(f"{data['company_name']} ({symbol.upper()})")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Sector: {data['sector']}")
                    st.write(f"Industry: {data['industry']}")
                    st.write(f"Employees: {data['employees']}")
                    st.write(f"Location: {data['city']}, {data['country']}")
                    st.write(f"Website: {data['website']}")
                
                with col2:
                    st.write("**Financial Metrics**")
                    st.write(f"Market Cap: {data['market_cap']}")
                    st.write(f"Enterprise Value: {data['enterprise_value']}")
                    st.write(f"P/E Ratio: {data['pe_ratio']}")
                    st.write(f"PEG Ratio: {data['peg_ratio']}")
                    st.write(f"Price to Book: {data['price_to_book']}")
                    st.write(f"Debt to Equity: {data['debt_to_equity']}")
                    st.write(f"Dividend Yield: {data['dividend_yield']}")
                
                st.subheader("Company Description")
                st.write(data['description'])
    
    def earnings_page(self):
        st.header("Earnings Data")
        
        symbol = st.text_input("Enter Stock Symbol", value="AAPL")
        
        if st.button("Get Earnings Data", type="primary"):
            with st.spinner("Fetching earnings data..."):
                data = self.agent.get_earnings_data(symbol.upper())
            
            if "error" in data:
                st.error(data["error"])
            else:
                st.subheader(f"Earnings for {symbol.upper()}")
                
                # Display earnings data
                if data['annual_earnings']:
                    st.write("**Annual Earnings**")
                    annual_df = pd.DataFrame(data['annual_earnings'])
                    st.dataframe(annual_df, use_container_width=True)
                
                if data['quarterly_earnings']:
                    st.write("**Quarterly Earnings**")
                    quarterly_df = pd.DataFrame(data['quarterly_earnings'])
                    st.dataframe(quarterly_df, use_container_width=True)
    
    def search_page(self):
        st.header("Stock Search")
        
        query = st.text_input("Search for stocks", help="Enter company name or symbol")
        
        if st.button("Search", type="primary") and query:
            with st.spinner("Searching..."):
                data = self.agent.search_stocks(query)
            
            if "error" in data:
                st.error(data["error"])
            elif data['results']:
                st.success(f"Found results for '{query}'")
                for result in data['results']:
                    st.write(f"**{result['symbol']}** - {result['name']}")
                    st.write(f"Sector: {result['sector']}, Industry: {result['industry']}")
                    st.write("---")
            else:
                st.warning(f"No results found for '{query}'")

def main():
    app = MarketDataStreamlit()
    app.run()

if __name__ == "__main__":
    main() 