from app.db.session import SessionLocal
from app.models.coffee_price_history import CoffeePriceHistory


DEFAULT_KEY = "COFFEE_C:USD_LB"


def main() -> None:
    db = SessionLocal()
    try:
        rows = (
            db.query(CoffeePriceHistory)
            .filter(CoffeePriceHistory.market_key.is_(None))
            .all()
        )
        for row in rows:
            row.market_key = DEFAULT_KEY
        db.commit()
        print(f"Updated coffee_price_history.market_key: {len(rows)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
