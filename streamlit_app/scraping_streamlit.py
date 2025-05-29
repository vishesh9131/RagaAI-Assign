import streamlit as st
from scraping_agent import ScrapingAgent

class ScrapingStreamlitApp:
    def __init__(self):
        self.agent = ScrapingAgent()

    def run(self):
        st.set_page_config(page_title="Web Scraping Agent", page_icon="🕸️", layout="wide")
        st.title("🕸️ Web Scraping Agent")

        st.sidebar.title("Scraping Options")
        app_mode = st.sidebar.selectbox(
            "Choose a scraping mode",
            ["Fetch HTML", "Extract Headlines", "Extract Generic Text", "Extract with Unstructured (Optional)"]
        )

        if app_mode == "Fetch HTML":
            self.page_fetch_html()
        elif app_mode == "Extract Headlines":
            self.page_extract_headlines()
        elif app_mode == "Extract Generic Text":
            self.page_extract_generic_text()
        elif app_mode == "Extract with Unstructured (Optional)":
            self.page_extract_unstructured()

    def page_fetch_html(self):
        st.header("Fetch Raw HTML Content")
        url = st.text_input("Enter URL to fetch HTML from:", "https://example.com")
        max_chars = st.number_input("Max characters to display:", min_value=100, max_value=10000, value=2000, step=100)

        if st.button("Fetch HTML", type="primary"):
            if not url:
                st.warning("Please enter a URL.")
                return
            
            with st.spinner(f"Fetching HTML from {url}..."):
                html_content = self.agent.fetch_html_content(url)
            
            if html_content:
                st.success("HTML Content Fetched Successfully!")
                st.code(html_content[:max_chars], language="html")
                if len(html_content) > max_chars:
                    st.caption(f"Showing first {max_chars} characters. Total length: {len(html_content)} chars.")
            else:
                st.error("Failed to fetch HTML. Check the URL and console for errors.")

    def page_extract_headlines(self):
        st.header("Extract Headlines")
        url = st.text_input("Enter URL to extract headlines from:", "https://news.google.com") # Example URL
        headline_tag = st.text_input("Headline HTML Tag (e.g., h1, h2, a):", "h3")
        headline_class = st.text_input("Headline CSS Class (optional):", "")
        max_headlines = st.number_input("Max headlines to display:", min_value=1, max_value=100, value=10, step=1)

        if st.button("Extract Headlines", type="primary"):
            if not url or not headline_tag:
                st.warning("Please enter a URL and a headline tag.")
                return

            with st.spinner(f"Extracting headlines from {url}..."):
                headlines = self.agent.extract_headlines(url, headline_tag, headline_class if headline_class else None)
            
            if headlines:
                st.success(f"Found {len(headlines)} headlines!")
                for i, h in enumerate(headlines[:max_headlines]):
                    st.markdown(f"{i+1}. {h}")
                if len(headlines) > max_headlines:
                    st.caption(f"Showing first {max_headlines} headlines.")
            else:
                st.warning("No headlines found with the specified criteria, or an error occurred.")

    def page_extract_generic_text(self):
        st.header("Extract Generic Paragraph Text")
        url = st.text_input("Enter URL to extract text from:", "https://en.wikipedia.org/wiki/Web_scraping")
        max_chars = st.number_input("Max characters to display:", min_value=100, max_value=10000, value=2000, step=100)

        if st.button("Extract Text", type="primary"):
            if not url:
                st.warning("Please enter a URL.")
                return

            with st.spinner(f"Extracting text from {url}..."):
                text_content = self.agent.extract_generic_text(url)
            
            if text_content:
                st.success("Text Extracted Successfully!")
                st.text_area("Extracted Text", text_content[:max_chars], height=300)
                if len(text_content) > max_chars:
                    st.caption(f"Showing first {max_chars} characters. Total length: {len(text_content)} chars.")
            else:
                st.error("Failed to extract text. Check the URL and console for errors.")

    def page_extract_unstructured(self):
        st.header("Extract with Unstructured.io (Optional)")
        st.markdown("""This feature requires the `unstructured` library. 
                    Install it with: `pip install "unstructured[html,local-inference]"`""")
        
        url = st.text_input("Enter URL to process with Unstructured:", "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000077/aapl-20230701.htm")

        if st.button("Extract with Unstructured", type="primary"):
            if not url:
                st.warning("Please enter a URL.")
                return
            
            with st.spinner(f"Processing {url} with Unstructured.io..."):
                try:
                    # The agent now handles fetching internally if a URL is given
                    elements = self.agent.extract_with_unstructured(url=url)
                except ImportError:
                    st.error("The 'unstructured' library is not installed. Please install it to use this feature: pip install \"unstructured[html,local-inference]\"")
                    return
                except Exception as e:
                    st.error(f"An error occurred while using unstructured: {e}")
                    return
            
            if elements:
                st.success(f"Successfully extracted {len(elements)} elements using Unstructured!")
                st.write("Sample of extracted elements:")
                for i, el in enumerate(elements[:5]): # Display first 5 elements
                    st.json({
                        "element_index": i + 1,
                        "type": el.get('type', 'N/A'),
                        "text_sample": el.get('text', '')[:200] + "..."
                    })
            else:
                st.warning("No elements extracted by Unstructured or an error occurred. Check console for details.")

if __name__ == "__main__":
    app = ScrapingStreamlitApp()
    app.run() 