<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=PRICEPULSE&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=32&desc=Track%20Amazon%20%26%20eBay%20prices%2C%20get%20alerted%20the%20moment%20they%20drop&descAlignY=55&descSize=14"/>

[![Live Demo](https://img.shields.io/badge/▶_Live_Demo-Visit_Now-6366f1?style=for-the-badge&logoColor=white)](https://pricepulse-swart.vercel.app)
[![GitHub Stars](https://img.shields.io/github/stars/trinathone/pricepulse?style=for-the-badge&color=f59e0b)](https://github.com/trinathone/pricepulse)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)

</div>

---

# PricePulse

A simple price tracking API that monitors product prices on Amazon and eBay, stores price history in a database, and alerts you when prices drop below your target.

> The live demo above is a static preview page. Run locally (below) for the full API + background scraper.

## What It Does

PricePulse automatically scrapes product prices from Amazon and eBay links. It stores all price records in a local SQLite database and exposes a REST API to:

- **Add products** to track (Amazon or eBay links)
- **Set target prices** for alerts
- **View price history** over time
- **Get real-time price updates** with one API call
- **Receive alerts** when prices drop below your target

The app scrapes prices automatically every 30 minutes and logs any price drops that match your alert thresholds.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python main.py
```

The API will start at `http://localhost:8000`

### 3. View the Interactive Docs

Open `http://localhost:8000/docs` in your browser. Swagger UI shows all endpoints with examples.

## How to Use

### Add a Product to Track

```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "url": "https://www.amazon.com/Apple-iPhone-15-128GB-Black/dp/B0CHX1F5X3",
    "source": "amazon",
    "target_price": 699
  }'
```

The app will start tracking this product. When the price drops to $699 or below, you'll see an alert in the logs.

### List All Products

```bash
curl "http://localhost:8000/products"
```

### Get Price History for a Product

```bash
curl "http://localhost:8000/products/1/history"
```

Returns all recorded prices with timestamps, oldest first.

### Manually Trigger a Scrape

```bash
curl -X POST "http://localhost:8000/scrape-now"
```

Useful for testing or getting immediate updates without waiting for the 30-minute interval.

### Update a Product

```bash
curl -X PATCH "http://localhost:8000/products/1" \
  -H "Content-Type: application/json" \
  -d '{
    "target_price": 650,
    "active": true
  }'
```

### Remove a Product

```bash
curl -X DELETE "http://localhost:8000/products/1"
```

### Check App Stats

```bash
curl "http://localhost:8000/stats"
```

Shows total products, active products, and price records stored.

## API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/products` | Add a new product to track |
| GET | `/products` | List all products |
| GET | `/products/{id}` | Get details for one product |
| PATCH | `/products/{id}` | Update product settings (target price, active status) |
| DELETE | `/products/{id}` | Stop tracking a product |
| GET | `/products/{id}/history` | Get all price records for a product |
| POST | `/scrape-now` | Trigger immediate price scrape for all products |
| GET | `/stats` | Get database statistics |

## How Scraping Works

The app uses **crawl4ai** to visit Amazon and eBay pages. It extracts prices using regex patterns and stores them in the database with timestamps.

### Automatic Scraping

- Runs every 30 minutes automatically
- Only scrapes active products
- Logs results to stdout
- Triggered at startup and continues until shutdown

### Price Alerts

When a product's current price is at or below your `target_price`, the app logs an alert showing:
- Product name
- Current price
- Target price
- How far below target (percentage)

Check the application logs to see alerts.

## Database

PricePulse uses SQLite by default. The database file is `pricepulse.db` and lives in the project root.

### Schema

**Products Table**
- `id` — unique product identifier
- `name` — product name
- `url` — Amazon or eBay product link
- `source` — "amazon" or "ebay"
- `target_price` — optional alert threshold
- `active` — whether to scrape this product
- `created_at` — when added to tracker

**Price History Table**
- `id` — unique record identifier
- `product_id` — reference to product
- `price` — recorded price in USD
- `scraped_at` — when this price was recorded

## Customization

### Change Scrape Interval

Open `main.py` and find this line:

```python
scheduler.add_job(scrape_job, "interval", minutes=30, ...)
```

Replace `30` with your preferred interval (in minutes). For example, `minutes=10` for every 10 minutes.

### Use a Different Database

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost/pricepulse"
python main.py
```

Supports any SQLAlchemy-compatible database (PostgreSQL, MySQL, etc).

### Run on a Different Port

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Troubleshooting

**"Product URL already tracked"**
- You've already added this product. Use GET `/products` to see existing ones.

**No prices scraped**
- Check the URL is valid and publicly accessible
- Some sites may require additional headers or JavaScript rendering that crawl4ai needs time to handle
- Check the logs for errors

**Scraper timeouts**
- Crawl4ai waits for page load. Large or slow sites may need more time.
- For slow sites, manual `/scrape-now` requests work better than auto-scraping.

**Alerts not appearing**
- Check the logs (stdout) — alerts print there
- Make sure the product has `active: true` and `target_price` is set
- Wait for the next scrape cycle or trigger `/scrape-now`

## Architecture

```
main.py              — FastAPI app and endpoints
models.py            — Database table definitions (SQLAlchemy)
database.py          — Database connection and session management
schemas.py           — API request/response models (Pydantic)
scraper.py           — Price extraction logic using crawl4ai
```

The app runs a background scheduler that calls the scraper on a fixed interval. All prices are persisted to SQLite.

## Production Notes

For production use:

1. Set `target_price` cautiously — don't set alerts for prices that rarely drop
2. Monitor the logs for scraper errors
3. Use a proper database (PostgreSQL) instead of SQLite for reliability
4. Run behind a reverse proxy or use environment-based secrets management
5. Consider rate-limiting if scraping many products frequently
6. Test URLs manually with `/scrape-now` before relying on auto-scraping

## Future Ideas

- Email notifications for price drops
- Slack/Discord webhook integration
- Price prediction and trend analysis
- Multi-user support with authentication
- Mobile app
- Bulk URL import from CSV

## License

MIT
