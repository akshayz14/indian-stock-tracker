"""
Script to fetch mutual fund data from mfapi.in and store in a separate SQLite database.
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from models import MutualFundAsset, MutualFundSuggestion, get_mutual_fund_session, Base, get_mutual_fund_engine

BASE_URL = "https://api.mfapi.in"

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

TOP_N = 50
MAX_WORKERS = 10

CATEGORIES = {
    "large_cap": "Large Cap",
    "mid_cap": "Mid Cap",
    "small_cap": "Small Cap",
    "debt": "Debt"
}


# ---------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------

session = requests.Session()

def get_json(url, retries=3):
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            if attempt == retries - 1:
                print(f"Failed: {url} -> {e}")
                return None

            time.sleep(1)

    return None


# ---------------------------------------------------------
# Get all schemes
# ---------------------------------------------------------

def get_all_schemes():
    print("Fetching mutual fund schemes...")

    all_schemes = []
    offset = 0
    limit = 1000

    while True:
        url = f"{BASE_URL}/mf?limit={limit}&offset={offset}"

        data = get_json(url)

        if not data:
            break

        all_schemes.extend(data)

        print(f"Fetched {len(all_schemes)} schemes...")

        if len(data) < limit:
            break

        offset += limit

    return all_schemes


# ---------------------------------------------------------
# Filter Direct Growth funds
# ---------------------------------------------------------

def is_direct_growth(name):
    name = name.upper()

    return (
        "DIRECT" in name
        and "GROWTH" in name
        and "IDCW" not in name
        and "DIVIDEND" not in name
    )


# ---------------------------------------------------------
# Determine category
# ---------------------------------------------------------

def get_category(meta_category):
    if not meta_category:
        return None

    category = meta_category.lower()

    if "large cap" in category:
        return "large_cap"

    if "mid cap" in category:
        return "mid_cap"

    if "small cap" in category:
        return "small_cap"

    # Debt contains many subcategories:
    # Liquid, Money Market, Corporate Bond,
    # Banking & PSU, Short Duration, etc.

    if "debt" in category:
        return "debt"

    return None


# ---------------------------------------------------------
# Fetch NAV history
# ---------------------------------------------------------

def get_nav_history(scheme_code):

    url = f"{BASE_URL}/mf/{scheme_code}"

    data = get_json(url)

    if not data:
        return None

    if data.get("status") != "SUCCESS":
        return None

    meta = data.get("meta", {})
    nav_data = data.get("data", [])

    if not nav_data:
        return None

    return {
        "meta": meta,
        "data": nav_data
    }


# ---------------------------------------------------------
# Convert NAV history into DataFrame
# ---------------------------------------------------------

def nav_dataframe(nav_data):

    df = pd.DataFrame(nav_data)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df["nav"] = pd.to_numeric(
        df["nav"],
        errors="coerce"
    )

    df = df.dropna(subset=["date", "nav"])

    df = df.sort_values("date")

    return df


# ---------------------------------------------------------
# Get NAV closest to requested date
# ---------------------------------------------------------

def get_nav_at_date(df, target_date):

    if df.empty:
        return None

    target_date = pd.Timestamp(target_date)

    eligible = df[df["date"] <= target_date]

    if eligible.empty:
        return None

    return eligible.iloc[-1]["nav"]


# ---------------------------------------------------------
# Calculate returns
# ---------------------------------------------------------

def calculate_returns(nav_data):

    df = nav_dataframe(nav_data)

    if df.empty:
        return None

    latest_date = df["date"].max()
    latest_nav = df.loc[
        df["date"] == latest_date, "nav"
    ].iloc[-1]

    result = {
        "latest_nav": latest_nav,
        "latest_date": latest_date
    }

    # 1 Year
    nav_1y = get_nav_at_date(
        df,
        latest_date - pd.DateOffset(years=1)
    )

    if nav_1y:
        result["return_1y"] = (
            (latest_nav / nav_1y) - 1
        ) * 100
    else:
        result["return_1y"] = None

    # 3 Year CAGR
    nav_3y = get_nav_at_date(
        df,
        latest_date - pd.DateOffset(years=3)
    )

    if nav_3y:
        result["return_3y"] = (
            (latest_nav / nav_3y) ** (1 / 3) - 1
        ) * 100
    else:
        result["return_3y"] = None

    # 5 Year CAGR
    nav_5y = get_nav_at_date(
        df,
        latest_date - pd.DateOffset(years=5)
    )

    if nav_5y:
        result["return_5y"] = (
            (latest_nav / nav_5y) ** (1 / 5) - 1
        ) * 100
    else:
        result["return_5y"] = None

    # Calculate volatility
    df["daily_return"] = df["nav"].pct_change()

    volatility = df["daily_return"].std()

    if pd.notna(volatility):
        result["volatility"] = volatility * np.sqrt(252) * 100
    else:
        result["volatility"] = None

    return result


# ---------------------------------------------------------
# Process one fund
# ---------------------------------------------------------

def process_fund(scheme):

    scheme_code = scheme.get("schemeCode")
    scheme_name = scheme.get("schemeName", "")

    if not scheme_code:
        return None

    if not is_direct_growth(scheme_name):
        return None

    data = get_nav_history(scheme_code)

    if not data:
        return None

    meta = data["meta"]

    category = get_category(
        meta.get("scheme_category", "")
    )

    if category is None:
        return None

    returns = calculate_returns(
        data["data"]
    )

    if not returns:
        return None

    return {
        "scheme_code": scheme_code,
        "scheme_name": meta.get("scheme_name"),
        "fund_house": meta.get("fund_house"),
        "category": category,
        **returns
    }


# ---------------------------------------------------------
# Score funds
# ---------------------------------------------------------

def calculate_score(df):

    # Require minimum historical data
    df = df.dropna(
        subset=[
            "return_1y",
            "return_3y"
        ]
    ).copy()

    if df.empty:
        return df

    # Percentile ranking
    df["score_1y"] = (
        df["return_1y"]
        .rank(pct=True)
        * 100
    )

    df["score_3y"] = (
        df["return_3y"]
        .rank(pct=True)
        * 100
    )

    # If 5Y exists, use it.
    if df["return_5y"].notna().sum() > 0:

        df["score_5y"] = (
            df["return_5y"]
            .rank(pct=True)
            * 100
        )

        df["score"] = (
            df["score_1y"] * 0.30
            + df["score_3y"] * 0.40
            + df["score_5y"].fillna(0) * 0.30
        )

    else:

        df["score"] = (
            df["score_1y"] * 0.40
            + df["score_3y"] * 0.60
        )

    return df


# ---------------------------------------------------------
# Initialize database
# ---------------------------------------------------------

def init_mutual_fund_db():
    """Initialize the mutual funds database."""
    engine = get_mutual_fund_engine()
    Base.metadata.create_all(engine)
    print("Mutual funds database initialized.")


# ---------------------------------------------------------
# Store fund in database
# ---------------------------------------------------------

def store_fund_in_db(fund_data, category):
    """Store a single fund in the mutual funds database."""
    session = get_mutual_fund_session()
    try:
        # Check if asset already exists
        existing_asset = session.query(MutualFundAsset).filter_by(
            scheme_code=fund_data["scheme_code"]
        ).first()

        if not existing_asset:
            # Create new asset
            asset = MutualFundAsset(
                scheme_code=fund_data["scheme_code"],
                scheme_name=fund_data["scheme_name"],
                fund_house=fund_data["fund_house"],
                type=category
            )
            session.add(asset)
            session.flush()  # Get the ID

            # Create suggestion
            suggestion = MutualFundSuggestion(
                asset_id=asset.id,
                date=datetime.now().date(),
                score=fund_data["score"],
                reasoning=f"Top {category.replace('_', ' ').title()} fund based on returns"
            )
            session.add(suggestion)
        else:
            # Update existing asset's suggestion
            latest_suggestion = session.query(MutualFundSuggestion).filter_by(
                asset_id=existing_asset.id
            ).order_by(MutualFundSuggestion.date.desc()).first()

            if latest_suggestion:
                latest_suggestion.score = fund_data["score"]
                latest_suggestion.date = datetime.now().date()
            else:
                suggestion = MutualFundSuggestion(
                    asset_id=existing_asset.id,
                    date=datetime.now().date(),
                    score=fund_data["score"],
                    reasoning=f"Top {category.replace('_', ' ').title()} fund based on returns"
                )
                session.add(suggestion)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error storing fund {fund_data.get('scheme_code')}: {e}")
        return False
    finally:
        session.close()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    # Initialize database
    init_mutual_fund_db()

    schemes = get_all_schemes()

    print(f"\nTotal schemes: {len(schemes)}")

    print("Processing funds...")

    results = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                process_fund,
                scheme
            )
            for scheme in schemes
        ]

        completed = 0

        for future in as_completed(futures):

            completed += 1

            try:
                result = future.result()

                if result:
                    results.append(result)

            except Exception as e:
                print(
                    f"Error processing fund: {e}"
                )

            if completed % 100 == 0:
                print(
                    f"Processed {completed}/{len(schemes)}"
                )

    print(
        f"\nValid funds found: {len(results)}"
    )

    df = pd.DataFrame(results)

    if df.empty:
        print("No funds found.")
        return

    # -----------------------------------------------------
    # Generate Top 50 for each category and store in DB
    # -----------------------------------------------------

    for category_key, category_name in CATEGORIES.items():

        # Map category keys to actual category values in the data
        category_mapping = {
            "large_cap": ["Equity Scheme - Large Cap Fund", "Equity Schemes - Large Cap Fund"],
            "mid_cap": ["Equity Scheme - Mid Cap Fund", "Equity Scheme - Large & Mid Cap Fund", "Equity Schemes - Mid Cap Fund"],
            "small_cap": ["Equity Scheme - Small Cap Fund", "Equity Schemes - Small Cap Fund"],
            "debt": ["debt"]
        }

        # Filter based on actual category values
        category_df = df[
            df["category"]
            .apply(
                lambda x:
                any(cat.lower() == category_key.lower() or category_key.replace("_", " ") in cat.lower()
                    for cat in ([x] if isinstance(x, str) else []))
            )
        ].copy()

        if category_df.empty:
            print(
                f"\nNo funds found for {category_name}"
            )
            continue

        category_df = calculate_score(
            category_df
        )

        category_df = category_df.sort_values(
            "score",
            ascending=False
        )

        top_funds = category_df.head(TOP_N)

        print(
            f"\n{'=' * 80}"
        )

        print(
            f"TOP {TOP_N} {category_name.upper()} FUNDS"
        )

        print(
            f"{'=' * 80}"
        )

        display_columns = [
            "scheme_name",
            "fund_house",
            "return_1y",
            "return_3y",
            "return_5y",
            "volatility",
            "score"
        ]

        print(
            top_funds[
                display_columns
            ].to_string(
                index=False,
                float_format=lambda x:
                    f"{x:.2f}"
            )
        )

        # Store in database
        stored_count = 0
        for _, fund in top_funds.iterrows():
            if store_fund_in_db(fund.to_dict(), category_key):
                stored_count += 1

        print(f"\nStored {stored_count} funds in database for {category_name}")

        # Save CSV
        filename = (
            f"top_{category_key}_funds.csv"
        )

        top_funds.to_csv(
            filename,
            index=False
        )

        print(f"Saved: {filename}")


if __name__ == "__main__":
    main()