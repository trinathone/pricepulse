from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Product, PriceHistory
from schemas import ProductCreate, ProductUpdate, ProductSchema, PriceAlertSchema
from scraper import scrape_all_products
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import logging

Base.metadata.create_all(bind=engine)
app = FastAPI(title="PricePulse", description="Track product prices and get alerts on price drops")

logger = logging.getLogger("pricepulse")
logging.basicConfig(level=logging.INFO)

scheduler = BackgroundScheduler()

def scrape_job(db: Session):
    try:
        alerts = asyncio.run(scrape_all_products(db))
        if alerts:
            logger.info(f"Price alerts triggered: {alerts}")
        else:
            logger.info("Scrape completed, no alerts")
    except Exception as e:
        logger.error(f"Scrape job failed: {e}")

@app.on_event("startup")
def startup():
    scheduler.add_job(scrape_job, "interval", minutes=30, args=[SessionLocal()], id="scrape_job")
    scheduler.start()
    logger.info("Scheduler started - scraping every 30 minutes")

from database import SessionLocal

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()
    logger.info("Scheduler stopped")

@app.get("/")
def root():
    return {"message": "PricePulse API - Track product prices and get alerts"}

@app.post("/products", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.url == product.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product URL already tracked")

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products", response_model=list[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.patch("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.dict(exclude_unset=True).items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

@app.get("/products/{product_id}/history")
def get_price_history(product_id: int, limit: int = 50, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = db.query(PriceHistory)\
        .filter(PriceHistory.product_id == product_id)\
        .order_by(PriceHistory.scraped_at.desc())\
        .limit(limit)\
        .all()

    return [{
        "price": h.price,
        "scraped_at": h.scraped_at
    } for h in reversed(history)]

@app.post("/scrape-now")
async def scrape_now(db: Session = Depends(get_db)):
    alerts = await scrape_all_products(db)
    return {
        "status": "completed",
        "alerts": alerts,
        "alert_count": len(alerts)
    }

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.active == True).count()
    total_prices = db.query(PriceHistory).count()

    return {
        "total_products": total_products,
        "active_products": active_products,
        "price_records": total_prices
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
