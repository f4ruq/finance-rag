import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
import config

logger = logging.getLogger("YFinanceCollector")

def scrape_article_text(url):
    """Scrapes the main text content from a given news URL."""
    if not url:
        return ""
    try:
        # User defined user agent from config for polite scraping
        headers = {'User-Agent': config.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Many Yahoo finance articles use 'caas-body' for the main content
        article_body = soup.find('div', class_='caas-body')
        
        # Generic fallback for Motley fool or others
        if not article_body:
            article_body = soup.find('article')
            
        if article_body:
            paragraphs = article_body.find_all('p')
            text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            return text
        else:
            return ""
    except Exception as e:
        logger.warning(f"Failed to scrape article at {url}: {e}")
        return ""

def run():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ticker_symbol = config.YFINANCE_TICKER
    out_dir = config.YFINANCE_DATA_DIR
    
    os.makedirs(out_dir, exist_ok=True)
    
    logger.info(f"Fetching data for {ticker_symbol} using yfinance...")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Basic Info & Valuation
    # info dictionary can be large, we'll extract key metrics useful for RAG
    info = ticker.info
    key_metrics = {
        "currentPrice": info.get("currentPrice"),
        "targetHighPrice": info.get("targetHighPrice"),
        "targetLowPrice": info.get("targetLowPrice"),
        "targetMeanPrice": info.get("targetMeanPrice"),
        "targetMedianPrice": info.get("targetMedianPrice"),
        "recommendationKey": info.get("recommendationKey"),
        "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions"),
        "forwardPE": info.get("forwardPE"),
        "trailingPE": info.get("trailingPE"),
        "profitMargins": info.get("profitMargins"),
        "ebitda": info.get("ebitda"),
        "revenueGrowth": info.get("revenueGrowth"),
        "operatingMargins": info.get("operatingMargins"),
        "shortName": info.get("shortName"),
        "sector": info.get("sector"),
    }
    
    # 2. Analyst Recommendations (Buy/Sell/Hold)
    # yfinance `.recommendations` gives a pandas dataframe
    recs_df = ticker.recommendations
    recs_summary = {}
    if recs_df is not None and not recs_df.empty:
        # Get the latest periods
        # Convert to dictionary oriented by records
        recs_summary = recs_df.to_dict(orient="records")
        
    # 3. Upgrades / Downgrades
    upgrades_df = ticker.upgrades_downgrades
    recent_upgrades = []
    if upgrades_df is not None and not upgrades_df.empty:
        # It's indexed by date, getting the last 20 upgrades for brief context
        recent = upgrades_df.tail(20)
        # reset index to bring datetime into the columns so we can serialize it
        recent = recent.reset_index()
        # Convert datetime to string
        recent['GradeDate'] = recent['GradeDate'].astype(str)
        recent_upgrades = recent.to_dict(orient="records")

    # 4. Recent News
    news = ticker.news
    formatted_news = []
    detailed_news = []
    
    for article in news:
        content = article.get("content") or {}
        provider = content.get("provider") or {}
        click_url = content.get("clickThroughUrl") or {}
        
        # Use pubDate or fallback
        pub_time = content.get("pubDate", "")
        article_url = click_url.get("url")
        title = content.get("title")
        publisher = provider.get("displayName")
        
        # Add basic info to summary
        formatted_news.append({
            "title": title,
            "publisher": publisher,
            "link": article_url,
            "published_at": pub_time
        })
        
        # Scrape full text for the RAG system
        logger.info(f"Scraping news: {title}")
        article_text = scrape_article_text(article_url)
        detailed_news.append({
            "title": title,
            "publisher": publisher,
            "link": article_url,
            "published_at": pub_time,
            "content": article_text
        })
        
    data = {
        "ticker": ticker_symbol,
        "collected_at": datetime.now().isoformat(),
        "key_metrics": key_metrics,
        "recommendation_summary": recs_summary,
        "recent_upgrades_downgrades": recent_upgrades,
        "recent_news_metadata": formatted_news
    }
    
    # Save the insight summary
    file_path = os.path.join(out_dir, f"{ticker_symbol}_yfinance_insight.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    logger.info(f"YFinance insight data saved to {file_path}")
    
    # Save the detailed scraped news
    news_file_path = os.path.join(out_dir, f"{ticker_symbol}_yfinance_news.json")
    detailed_news_data = {
        "ticker": ticker_symbol,
        "collected_at": datetime.now().isoformat(),
        "articles": detailed_news
    }
    with open(news_file_path, "w", encoding="utf-8") as f:
        json.dump(detailed_news_data, f, indent=4, ensure_ascii=False)
        
    logger.info(f"YFinance detailed news saved to {news_file_path}")

if __name__ == "__main__":
    run()
