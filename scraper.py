import re
from crawl4ai import AsyncWebCrawler
from sqlalchemy.orm import Session
from models import Product, PriceHistory
from datetime import datetime
import asyncio

async def scrape_amazon_price(url: str) -> float | None:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, bypass_cache=True)
        if result.success:
            text = result.cleaned_html or result.html
            prices = re.findall(r'\$[\d,]+\.?\d*', text)
            if prices:
                try:
                    price_str = prices[0].replace('$', '').replace(',', '')
                    return float(price_str)
                except ValueError:
                    return None
    return None

async def scrape_ebay_price(url: str) -> float | None:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, bypass_cache=True)
        if result.success:
            text = result.cleaned_html or result.html
            prices = re.findall(r'\$[\d,]+\.?\d*', text)
            if prices:
                try:
                    price_str = prices[0].replace('$', '').replace(',', '')
                    return float(price_str)
                except ValueError:
                    return None
    return None

async def scrape_product(product: Product) -> float | None:
    if product.source.lower() == "amazon":
        return await scrape_amazon_price(product.url)
    elif product.source.lower() == "ebay":
        return await scrape_ebay_price(product.url)
    return None

async def scrape_all_products(db: Session) -> list[dict]:
    products = db.query(Product).filter(Product.active == True).all()
    alerts = []

    for product in products:
        price = await scrape_product(product)
        if price:
            history = PriceHistory(product_id=product.id, price=price, scraped_at=datetime.utcnow())
            db.add(history)

            if product.target_price and price <= product.target_price:
                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_price": price,
                    "target_price": product.target_price,
                    "drop_percentage": round(((product.target_price - price) / product.target_price) * 100, 2)
                })

    db.commit()
    return alerts
