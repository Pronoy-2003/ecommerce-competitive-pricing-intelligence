"""
====================================================================
E-COMMERCE DATA COLLECTION PIPELINE
====================================================================

PROJECT:
E-commerce Competitive Pricing & Product Intelligence

--------------------------------------------------------------------
PROJECT PURPOSE
--------------------------------------------------------------------

This script collects real-world product data from two major
e-commerce marketplaces:

    1. Amazon
    2. Flipkart

The data is collected using the QuickCommerce API's
multi-platform product search endpoint.

The collected data is intended for analyzing:

    - Product pricing
    - MRP
    - Selling price
    - Discount percentage
    - Product availability
    - Product ratings
    - Review counts
    - Brand-level competitiveness
    - Category-level competitiveness
    - City-level pricing differences

--------------------------------------------------------------------
DATA SOURCE
--------------------------------------------------------------------

QuickCommerce API

Documentation:
https://quickcommerceapi.com/docs

The API provides product search data across multiple Indian
marketplaces and quick-commerce platforms.

For this project, ONLY the following e-commerce marketplaces
are used:

    - Amazon
    - Flipkart

--------------------------------------------------------------------
CITIES
--------------------------------------------------------------------

Data is collected for five Indian cities:

    1. Bengaluru
    2. Delhi
    3. Mumbai
    4. Hyderabad
    5. Guwahati

Latitude and longitude are supplied to the API so that
location-specific product information can be retrieved.

--------------------------------------------------------------------
DATA COLLECTION METHOD
--------------------------------------------------------------------

Python
   ↓
HTTP API Request
   ↓
QuickCommerce API
   ↓
JSON Response
   ↓
Response Parsing
   ↓
Pandas DataFrame
   ↓
Data Cleaning
   ↓
Duplicate Detection
   ↓
CSV Dataset

--------------------------------------------------------------------
API CREDIT USAGE
--------------------------------------------------------------------

The API charges one credit per platform requested.

For one search query:

    Amazon + Flipkart

requires approximately:

    2 credits

For 20 search queries:

    20 × 2 = 40 credits

Therefore, each city collection batch in this script is
designed around approximately 40 API credits.

--------------------------------------------------------------------
IMPORTANT
--------------------------------------------------------------------

This script is designed to collect ONE CITY at a time.

Change:

    CITY_TO_COLLECT

to collect another city.

The API key must NOT be hardcoded into this file.

Set it as an environment variable:

    QUICKCOMMERCE_API_KEY

Never upload your API key to GitHub.

--------------------------------------------------------------------
FINAL PROJECT DATA
--------------------------------------------------------------------

The completed project contains approximately:

    4,679 observations

across:

    5 cities
    2 e-commerce marketplaces

--------------------------------------------------------------------
BUSINESS OBJECTIVE
--------------------------------------------------------------------

The final dataset will be used to identify:

    - Pricing gaps between marketplaces
    - Discount patterns
    - Category competitiveness
    - Brand-level pricing differences
    - Product availability differences
    - Geographic pricing differences

====================================================================
"""

# ================================================================
# 1. IMPORT REQUIRED LIBRARIES
# ================================================================

import os
import re
import time
from datetime import datetime

import requests
import pandas as pd
from tqdm import tqdm


# ================================================================
# 2. API CONFIGURATION
# ================================================================

# QuickCommerce API base URL.
BASE_URL = "https://api.quickcommerceapi.com"


# Read the API key from an environment variable.
#
# This is important for GitHub security.
# NEVER write the actual API key directly in this script.

API_KEY = os.getenv(
    "QUICKCOMMERCE_API_KEY"
)

if not API_KEY:

    raise ValueError(
        "QUICKCOMMERCE_API_KEY environment variable "
        "was not found."
    )


# API authentication header.
HEADERS = {
    "X-API-Key": API_KEY
}


# ================================================================
# 3. CITY CONFIGURATION
# ================================================================

# Latitude and longitude are used to retrieve
# location-specific product results.

CITIES = {

    "Bengaluru": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },

    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },

    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },

    "Hyderabad": {
        "latitude": 17.3850,
        "longitude": 78.4867
    },

    "Guwahati": {
        "latitude": 26.1445,
        "longitude": 91.7362
    }
}


# ================================================================
# 4. SELECT CITY
# ================================================================

# The script intentionally collects ONE CITY at a time.
#
# Change this value when running the pipeline for another city.

CITY_TO_COLLECT = "Guwahati"


if CITY_TO_COLLECT not in CITIES:

    raise ValueError(
        f"Invalid city: {CITY_TO_COLLECT}. "
        f"Available cities: {list(CITIES.keys())}"
    )


CITY_INFO = CITIES[
    CITY_TO_COLLECT
]


# ================================================================
# 5. E-COMMERCE PLATFORMS
# ================================================================

# ONLY E-COMMERCE MARKETPLACES ARE INCLUDED HERE.

PLATFORMS = [
    "Amazon",
    "Flipkart"
]


# ================================================================
# 6. PRODUCT SEARCH QUERIES
# ================================================================

# These queries cover several major e-commerce categories.

SEARCH_QUERIES = [

    # ------------------------------------------------------------
    # Smartphones
    # ------------------------------------------------------------

    "Samsung Galaxy smartphone",
    "OnePlus smartphone",
    "Xiaomi Redmi smartphone",
    "Poco smartphone",

    # ------------------------------------------------------------
    # Laptops
    # ------------------------------------------------------------

    "Lenovo IdeaPad laptop",
    "HP 15 laptop",
    "Dell Vostro laptop",
    "Acer Aspire laptop",

    # ------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------

    "boAt earbuds",
    "Realme earbuds",
    "JBL headphones",
    "Sony headphones",

    # ------------------------------------------------------------
    # Smartwatches
    # ------------------------------------------------------------

    "Fire Boltt smartwatch",
    "Noise smartwatch",
    "Samsung smartwatch",
    "Titan smartwatch",

    # ------------------------------------------------------------
    # Televisions
    # ------------------------------------------------------------

    "Samsung 43 inch TV",
    "LG 43 inch TV",
    "Sony 43 inch TV",
    "TCL 43 inch TV"
]


# ================================================================
# 7. CATEGORY MAPPING
# ================================================================

# Converts search queries into standardized business categories.

CATEGORY_MAP = {

    "Samsung Galaxy smartphone":
        "Smartphones",

    "OnePlus smartphone":
        "Smartphones",

    "Xiaomi Redmi smartphone":
        "Smartphones",

    "Poco smartphone":
        "Smartphones",

    "Lenovo IdeaPad laptop":
        "Laptops",

    "HP 15 laptop":
        "Laptops",

    "Dell Vostro laptop":
        "Laptops",

    "Acer Aspire laptop":
        "Laptops",

    "boAt earbuds":
        "Headphones/Earbuds",

    "Realme earbuds":
        "Headphones/Earbuds",

    "JBL headphones":
        "Headphones/Earbuds",

    "Sony headphones":
        "Headphones/Earbuds",

    "Fire Boltt smartwatch":
        "Smartwatches",

    "Noise smartwatch":
        "Smartwatches",

    "Samsung smartwatch":
        "Smartwatches",

    "Titan smartwatch":
        "Smartwatches",

    "Samsung 43 inch TV":
        "Televisions",

    "LG 43 inch TV":
        "Televisions",

    "Sony 43 inch TV":
        "Televisions",

    "TCL 43 inch TV":
        "Televisions"
}


# ================================================================
# 8. TEXT NORMALIZATION
# ================================================================

def normalize_text(value):
    """
    Standardizes text for duplicate detection.

    Example:

        Samsung Galaxy S25 256GB

    becomes:

        samsung galaxy s25 256gb
    """

    if pd.isna(value):
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ================================================================
# 9. CHECK API CREDITS
# ================================================================

def check_credits():
    """
    Checks the current API credit balance.

    The /v1/credits endpoint is free according to the API
    documentation.
    """

    response = requests.get(
        f"{BASE_URL}/v1/credits",
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    credits = data.get(
        "summary",
        {}
    ).get(
        "total_available"
    )

    print(
        f"Available API credits: {credits}"
    )

    return credits


# ================================================================
# 10. PRODUCT SEARCH FUNCTION
# ================================================================

def search_products(
    query,
    city_info,
    platforms
):
    """
    Searches Amazon and Flipkart using groupsearch.

    Credit cost:

        1 credit per platform

    Therefore:

        Amazon + Flipkart = approximately 2 credits
    """

    url = (
        f"{BASE_URL}/v1/groupsearch"
    )

    params = {

        "q":
            query,

        "lat":
            city_info["latitude"],

        "lon":
            city_info["longitude"],

        "platforms":
            ",".join(platforms)
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=60
    )

    if response.status_code != 200:

        print(
            f"API ERROR | "
            f"Query={query} | "
            f"Status={response.status_code}"
        )

        print(
            response.text[:500]
        )

        return None

    return response.json()


# ================================================================
# 11. PARSE API RESPONSE
# ================================================================

def parse_response(
    response_data,
    query,
    city
):
    """
    Converts the API JSON response into structured records.
    """

    rows = []

    if response_data is None:
        return rows

    data = response_data.get(
        "data",
        {}
    )

    results = data.get(
        "results",
        {}
    )

    # Iterate through each marketplace.
    for platform, products in results.items():

        if not isinstance(
            products,
            list
        ):
            continue

        # Iterate through products.
        for product in products:

            mrp = product.get(
                "mrp"
            )

            selling_price = product.get(
                "offer_price"
            )

            # ----------------------------------------------------
            # Calculate discount percentage
            # ----------------------------------------------------

            discount_pct = None

            try:

                if (
                    mrp is not None
                    and selling_price is not None
                    and float(mrp) > 0
                ):

                    discount_pct = (
                        (
                            float(mrp)
                            - float(selling_price)
                        )
                        / float(mrp)
                    ) * 100

            except (
                ValueError,
                TypeError
            ):

                discount_pct = None


            # ----------------------------------------------------
            # Store product record
            # ----------------------------------------------------

            rows.append({

                "platform":
                    platform,

                "product_id":
                    product.get("id"),

                "product_name":
                    product.get("name"),

                "brand":
                    product.get("brand"),

                "category":
                    CATEGORY_MAP.get(
                        query
                    ),

                "variant":
                    product.get("quantity"),

                "mrp":
                    mrp,

                "selling_price":
                    selling_price,

                "discount_pct":
                    discount_pct,

                "rating":
                    product.get("rating"),

                "review_count":
                    product.get(
                        "ratingCount",
                        product.get(
                            "rating_count"
                        )
                    ),

                "availability":
                    product.get(
                        "available"
                    ),

                "inventory":
                    product.get(
                        "inventory"
                    ),

                "seller":
                    None,

                "product_url":
                    product.get(
                        "deeplink"
                    ),

                "search_query":
                    query,

                "city":
                    city,

                "latitude":
                    CITIES[city]["latitude"],

                "longitude":
                    CITIES[city]["longitude"],

                "collection_timestamp":
                    datetime.now().isoformat()
            })

    return rows


# ================================================================
# 12. CREATE DUPLICATE KEY
# ================================================================

def create_duplicate_key(row):
    """
    Creates a business-level duplicate key.

    Grain:

        Platform
        + City
        + Brand
        + Product
        + Variant

    City is included intentionally.

    Example:

        Amazon + Samsung TV + Mumbai

    and

        Amazon + Samsung TV + Guwahati

    are treated as separate observations because they represent
    different geographic markets.
    """

    return "|".join([

        normalize_text(
            row.get("platform")
        ),

        normalize_text(
            row.get("city")
        ),

        normalize_text(
            row.get("brand")
        ),

        normalize_text(
            row.get("product_name")
        ),

        normalize_text(
            row.get("variant")
        )
    ])


# ================================================================
# 13. MAIN COLLECTION FUNCTION
# ================================================================

def collect_data():

    print("=" * 70)
    print("E-COMMERCE DATA COLLECTION")
    print("=" * 70)

    print(
        f"City       : {CITY_TO_COLLECT}"
    )

    print(
        f"Platforms  : {', '.join(PLATFORMS)}"
    )

    print(
        f"Queries    : {len(SEARCH_QUERIES)}"
    )

    expected_cost = (
        len(SEARCH_QUERIES)
        * len(PLATFORMS)
    )

    print(
        f"Expected API credits: {expected_cost}"
    )

    print("=" * 70)


    # ------------------------------------------------------------
    # Check available credits before making paid requests.
    # ------------------------------------------------------------

    credits = check_credits()

    if credits is not None:

        if credits < expected_cost:

            raise RuntimeError(
                f"Insufficient credits. "
                f"Required: {expected_cost}. "
                f"Available: {credits}."
            )


    # ------------------------------------------------------------
    # Store all API results.
    # ------------------------------------------------------------

    all_rows = []


    # ------------------------------------------------------------
    # Execute searches.
    # ------------------------------------------------------------

    for query in tqdm(
        SEARCH_QUERIES,
        desc=f"Collecting {CITY_TO_COLLECT}"
    ):

        response = search_products(
            query=query,
            city_info=CITY_INFO,
            platforms=PLATFORMS
        )

        rows = parse_response(
            response_data=response,
            query=query,
            city=CITY_TO_COLLECT
        )

        all_rows.extend(
            rows
        )

        # Small pause between requests.
        time.sleep(1)


    # ------------------------------------------------------------
    # Convert records to DataFrame.
    # ------------------------------------------------------------

    df = pd.DataFrame(
        all_rows
    )

    print(
        f"\nRaw rows collected: {len(df)}"
    )


    if df.empty:

        print(
            "No records were returned."
        )

        return df


    # ------------------------------------------------------------
    # Create duplicate key.
    # ------------------------------------------------------------

    df["duplicate_key"] = (
        df.apply(
            create_duplicate_key,
            axis=1
        )
    )


    # ------------------------------------------------------------
    # Remove duplicates within this collection batch.
    # ------------------------------------------------------------

    before = len(df)

    df = (
        df
        .drop_duplicates(
            subset=[
                "duplicate_key"
            ]
        )
        .reset_index(drop=True)
    )

    after = len(df)

    print(
        f"Duplicates removed: {before - after}"
    )

    print(
        f"Unique records: {after}"
    )


    # ------------------------------------------------------------
    # Remove technical duplicate key.
    # ------------------------------------------------------------

    df = df.drop(
        columns=[
            "duplicate_key"
        ]
    )


    # ------------------------------------------------------------
    # Create output directory.
    # ------------------------------------------------------------

    os.makedirs(
        "data/raw",
        exist_ok=True
    )


    # ------------------------------------------------------------
    # Save city-level CSV.
    # ------------------------------------------------------------

    output_file = (
        f"data/raw/"
        f"ecommerce_"
        f"{CITY_TO_COLLECT.lower()}.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nDataset saved to: {output_file}"
    )


    # ------------------------------------------------------------
    # Basic validation.
    # ------------------------------------------------------------

    print("\nPlatform distribution:")

    print(
        df["platform"].value_counts()
    )

    print("\nCategory distribution:")

    print(
        df["category"].value_counts()
    )

    print("\nMissing values:")

    print(
        df.isna().sum()
    )


    return df


# ================================================================
# 14. SCRIPT ENTRY POINT
# ================================================================

if __name__ == "__main__":

    ecommerce_data = collect_data()