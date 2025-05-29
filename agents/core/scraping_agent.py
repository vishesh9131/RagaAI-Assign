import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

class ScrapingAgent:
    """
    An agent responsible for scraping web content like articles, headlines,
    filings, etc., using tools like requests and BeautifulSoup.
    Can be extended with libraries like 'unstructured' for more advanced parsing.
    """

    def __init__(self):
        """
        Initialize the scraping agent with a requests session.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1", # Do Not Track
            "Upgrade-Insecure-Requests": "1"
        })

    def fetch_html_content(self, url: str) -> Optional[str]:
        """
        Fetches the HTML content of a given URL.

        Args:
            url: The URL to fetch.

        Returns:
            The HTML content as a string, or None if an error occurs.
        """
        try:
            response = self.session.get(url, timeout=15) # Increased timeout
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    def get_beautifulsoup_object(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches HTML from a URL and returns a BeautifulSoup object.

        Args:
            url: The URL to fetch and parse.

        Returns:
            A BeautifulSoup object, or None if an error occurs.
        """
        html_content = self.fetch_html_content(url)
        if html_content:
            return BeautifulSoup(html_content, "html.parser")
        return None

    def extract_headlines(self, url: str, headline_tag: str, headline_class: Optional[str] = None) -> List[str]:
        """
        Extracts headlines from a given URL based on HTML tag and optional class.

        Args:
            url: The URL to scrape headlines from.
            headline_tag: The HTML tag for headlines (e.g., 'h1', 'h2', 'a').
            headline_class: The CSS class of the headline elements (optional).

        Returns:
            A list of headline texts.
        """
        soup = self.get_beautifulsoup_object(url)
        headlines = []
        if soup:
            if headline_class:
                elements = soup.find_all(headline_tag, class_=headline_class)
            else:
                elements = soup.find_all(headline_tag)
            
            for element in elements:
                headlines.append(element.get_text(strip=True))
        return headlines

    def extract_generic_text(self, url: str) -> Optional[str]:
        """
        Extracts all paragraph text from a given URL.
        A simple example; more sophisticated extraction might be needed for complex sites.

        Args:
            url: The URL to extract text from.

        Returns:
            A concatenated string of all paragraph texts, or None.
        """
        soup = self.get_beautifulsoup_object(url)
        if soup:
            paragraphs = soup.find_all('p')
            return "\n".join([p.get_text(strip=True) for p in paragraphs])
        return None

    def extract_with_unstructured(self, url: Optional[str] = None, html_content: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Uses the 'unstructured' library to extract elements from a URL or direct HTML content.
        Note: 'unstructured' library needs to be installed.
        If html_content is provided, it's used directly. Otherwise, url is fetched.
        """
        if not html_content and url:
            print(f"Fetching HTML for unstructured via ScrapingAgent: {url}")
            html_content = self.fetch_html_content(url)
            if not html_content:
                # Error message already printed by fetch_html_content
                return None
        elif not html_content and not url:
            print("Error: Must provide either url or html_content to extract_with_unstructured.")
            return None

        try:
            from unstructured.partition.html import partition_html
            # Using partition_html with text input
            elements = partition_html(text=html_content)
            return [el.to_dict() for el in elements]
        except ImportError:
            print("The 'unstructured' library is not installed. Please install it to use this feature: pip install \"unstructured[html,local-inference]\"")
            return None
        except Exception as e:
            print(f"Error using unstructured: {e}")
            return None

if __name__ == '__main__':
    # Example Usage
    agent = ScrapingAgent()

    # Example 1: Fetch HTML
    # html = agent.fetch_html_content("https://news.google.com")
    # if html:
    #     print(f"Fetched HTML (first 500 chars):\n{html[:500]}\n")

    # Example 2: Extract headlines (adjust tag/class for a specific site)
    # For instance, to get headlines from a news site, you'd inspect its HTML
    # to find the correct tags and classes. This is a generic example.
    # Let's try a site where 'h3' might be common for article titles
    # headlines = agent.extract_headlines("https://www.reuters.com/news/archive/businessNews", "h3") # This is an example, actual tags may vary
    # print("Attempting to extract headlines (example):")
    # if headlines:
    #     for i, headline in enumerate(headlines[:5]):
    #         print(f"{i+1}. {headline}")
    # else:
    #     print("Could not extract headlines with the generic example.")
    # print("\n")
    
    # Example 3: Extract generic paragraph text
    # text_content = agent.extract_generic_text("https://en.wikipedia.org/wiki/Web_scraping")
    # print("Extracted generic text (first 500 chars):")
    # if text_content:
    #     print(f"{text_content[:500]}...")
    # else:
    #     print("Could not extract generic text.")
    # print("\n")

    # Example 4: Using unstructured (if installed)
    print("Attempting to extract with unstructured (if installed):")
    # Test with a more permissive URL first if SEC is still an issue
    # test_url_unstructured = "https://www.example.com"
    # print(f"Using test URL for unstructured: {test_url_unstructured}")
    # unstructured_elements = agent.extract_with_unstructured(url=test_url_unstructured)

    sec_url = "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000077/aapl-20230701.htm"
    print(f"Attempting unstructured on SEC URL: {sec_url}")
    unstructured_elements = agent.extract_with_unstructured(url=sec_url)

    if unstructured_elements:
        print(f"Extracted {len(unstructured_elements)} elements using unstructured.")
        for i, el in enumerate(unstructured_elements[:3]): # Print first 3 elements
            print(f"Element {i+1} type: {el.get('type', 'N/A')}, Text sample: {el.get('text', '')[:100]}...")
    else:
        print("Skipping unstructured example or an error occurred.")
    pass 