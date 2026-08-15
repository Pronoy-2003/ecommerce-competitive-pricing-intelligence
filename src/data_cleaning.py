"""
====================================================================
E-COMMERCE DATA CLEANING PIPELINE
====================================================================

PROJECT:
E-Commerce Competitive Pricing & Product Intelligence

PURPOSE:
--------------------------------------------------------------------
This script cleans and validates the raw E-Commerce master dataset
collected from Amazon and Flipkart across five Indian cities:

    1. Bengaluru
    2. Delhi
    3. Mumbai
    4. Hyderabad
    5. Guwahati

The raw dataset contains 4,679 product-level observations.

The purpose of this script is to transform the raw API-collected
dataset into a reliable, analysis-ready dataset for:

    - Exploratory Data Analysis
    - SQL Business Analysis
    - Competitive Pricing Analysis
    - Power BI Dashboard
    - Business Recommendations

CLEANING PROCESS:
--------------------------------------------------------------------
1. Load raw dataset
2. Inspect the raw data
3. Standardize column names
4. Clean text fields
5. Convert data types
6. Remove columns with 100% missing values
7. Remove constant/non-informative columns
8. Handle missing brand and variant values
9. Preserve legitimate missing ratings/review counts
10. Remove invalid zero-price records
11. Recalculate discount percentage
12. Remove exact duplicate rows
13. Remove repeated search-query observations
14. Validate ratings
15. Identify price outliers
16. Validate discount percentage
17. Perform final data-quality checks
18. Save cleaned dataset
19. Save cleaning report

IMPORTANT BUSINESS DECISIONS:
--------------------------------------------------------------------
- Missing brand values are replaced with "Unknown".
- Missing variant values are replaced with "Not Specified".
- Missing ratings and review counts are preserved.
- Products with MRP <= 0 or selling price <= 0 are removed because
  they cannot be used for meaningful price analysis.
- Repeated products caused by different search queries are
  deduplicated using:

        platform + city + product_id

- Potential price outliers are FLAGGED, not deleted, because
  expensive products may be legitimate observations.
- The raw dataset is never overwritten.

DATA SOURCE:
--------------------------------------------------------------------
QuickCommerce API

MARKETPLACES:
--------------------------------------------------------------------
- Amazon
- Flipkart

OUTPUT:
--------------------------------------------------------------------
Cleaned dataset:

    data/processed/ecommerce_cleaned.csv

Cleaning report:

    data/processed/ecommerce_cleaning_report.csv

====================================================================
"""


# ================================================================
# 1. IMPORT LIBRARIES
# ================================================================

import os
import numpy as np
import pandas as pd


# ================================================================
# 2. FILE PATH CONFIGURATION
# ================================================================

# Complete raw master dataset.
INPUT_FILE = "data/raw/ecommerce/ecommerce_master.csv"

# Directory for processed data.
OUTPUT_DIR = "data/processed"

# Final cleaned dataset.
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "ecommerce_cleaned.csv"
)

# Data-quality/cleaning report.
REPORT_FILE = os.path.join(
    OUTPUT_DIR,
    "ecommerce_cleaning_report.csv"
)


# ================================================================
# 3. LOAD RAW DATA
# ================================================================

def load_data(file_path):
    """
    Load the raw E-Commerce dataset.

    Parameters
    ----------
    file_path : str
        Path to the raw CSV file.

    Returns
    -------
    pandas.DataFrame
        Raw E-Commerce dataset.
    """

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    df = pd.read_csv(
        file_path
    )

    print("\n" + "=" * 70)
    print("RAW DATA LOADED")
    print("=" * 70)

    print(
        f"Rows    : {df.shape[0]}"
    )

    print(
        f"Columns : {df.shape[1]}"
    )

    return df


# ================================================================
# 4. INITIAL DATA INSPECTION
# ================================================================

def inspect_data(df):
    """
    Inspect the raw dataset before performing cleaning.

    This step helps identify:
        - Dataset dimensions
        - Data types
        - Missing values
        - Duplicate rows
        - Numerical statistics
    """

    print("\n" + "=" * 70)
    print("INITIAL DATA INSPECTION")
    print("=" * 70)

    print("\nColumn names:")
    print(
        df.columns.tolist()
    )

    print("\nData types:")
    print(
        df.dtypes
    )

    print("\nMissing values:")
    print(
        df.isna().sum()
    )

    print("\nExact duplicate rows:")
    print(
        df.duplicated().sum()
    )

    print("\nNumerical summary:")
    print(
        df.describe(
            include="all"
        ).T
    )


# ================================================================
# 5. STANDARDIZE COLUMN NAMES
# ================================================================

def standardize_column_names(df):
    """
    Standardize column names into lowercase snake_case.

    Example:

        Selling Price
        selling-price
        Selling_Price

    become:

        selling_price
    """

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(
            " ",
            "_"
        )
        .str.replace(
            "-",
            "_"
        )
    )

    return df


# ================================================================
# 6. CLEAN TEXT COLUMNS
# ================================================================

def clean_text_columns(df):
    """
    Clean textual and categorical fields.

    Operations:
        - Remove leading/trailing spaces
        - Replace repeated spaces
        - Convert empty strings to missing values
        - Standardize platform and city names
    """

    text_columns = [
        "platform",
        "product_id",
        "product_name",
        "brand",
        "category",
        "subcategory",
        "model",
        "variant",
        "seller",
        "product_url",
        "search_query",
        "city"
    ]

    for column in text_columns:

        if column not in df.columns:
            continue

        # Convert empty/whitespace-only strings to NaN.
        df[column] = (
            df[column]
            .replace(
                r"^\s*$",
                np.nan,
                regex=True
            )
        )

        # Strip leading/trailing whitespace.
        if df[column].dtype == "object":

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

        # Replace repeated whitespace with a single space.
        if pd.api.types.is_string_dtype(
            df[column]
        ):

            df[column] = (
                df[column]
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
            )

    # ------------------------------------------------------------
    # Standardize marketplace names.
    # ------------------------------------------------------------

    if "platform" in df.columns:

        df["platform"] = (
            df["platform"]
            .str.strip()
            .str.title()
        )

    # ------------------------------------------------------------
    # Standardize city names.
    # ------------------------------------------------------------

    if "city" in df.columns:

        df["city"] = (
            df["city"]
            .str.strip()
            .str.title()
        )

    return df


# ================================================================
# 7. CONVERT DATA TYPES
# ================================================================

def convert_data_types(df):
    """
    Convert fields into appropriate analytical data types.
    """

    # ------------------------------------------------------------
    # Numeric columns.
    # ------------------------------------------------------------

    numeric_columns = [
        "mrp",
        "selling_price",
        "discount_pct",
        "rating",
        "review_count",
        "inventory",
        "latitude",
        "longitude"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # ------------------------------------------------------------
    # Boolean availability.
    # ------------------------------------------------------------

    if "availability" in df.columns:

        df["availability"] = (
            df["availability"]
            .astype("boolean")
        )

    # ------------------------------------------------------------
    # Timestamp.
    # ------------------------------------------------------------

    if "scrape_timestamp" in df.columns:

        df["scrape_timestamp"] = (
            pd.to_datetime(
                df["scrape_timestamp"],
                errors="coerce"
            )
        )

    return df


# ================================================================
# 8. REMOVE COMPLETELY MISSING COLUMNS
# ================================================================

def remove_completely_missing_columns(df):
    """
    Remove columns where 100% of the values are missing.

    In the collected dataset:

        subcategory = 100% missing
        model       = 100% missing
        seller      = 100% missing

    These columns contain no analytical information and therefore
    are removed from the cleaned dataset.
    """

    completely_missing = [
        column
        for column in df.columns
        if df[column].isna().all()
    ]

    print("\n" + "=" * 70)
    print("100% MISSING COLUMN REMOVAL")
    print("=" * 70)

    if completely_missing:

        print(
            "Columns removed:"
        )

        for column in completely_missing:

            print(
                f" - {column}"
            )

        df = df.drop(
            columns=completely_missing
        )

    else:

        print(
            "No completely missing columns found."
        )

    return df


# ================================================================
# 9. REMOVE CONSTANT / NON-INFORMATIVE COLUMNS
# ================================================================

def remove_constant_columns(df):
    """
    Remove columns containing only one unique value.

    In the collected dataset:

        availability = True for every row
        inventory    = 1 for every row

    Since these fields have no variation, they cannot explain
    differences between products and are removed from the analytical
    dataset.

    The raw dataset remains unchanged.
    """

    constant_columns = []

    for column in df.columns:

        if df[column].nunique(
            dropna=False
        ) <= 1:

            constant_columns.append(
                column
            )

    print("\n" + "=" * 70)
    print("CONSTANT COLUMN ANALYSIS")
    print("=" * 70)

    if constant_columns:

        print(
            "Constant columns removed:"
        )

        for column in constant_columns:

            print(
                f" - {column}"
            )

        df = df.drop(
            columns=constant_columns
        )

    else:

        print(
            "No constant columns found."
        )

    return df


# ================================================================
# 10. HANDLE MISSING BRAND
# ================================================================

def handle_missing_brand(df):
    """
    Replace missing brand values with 'Unknown'.

    IMPORTANT:
    We do not infer the brand from search_query.

    Example:

        search_query = Samsung smartphone

    does NOT necessarily mean:

        brand = Samsung

    Therefore, if the API did not return a brand, the value is
    explicitly labelled as Unknown.
    """

    if "brand" not in df.columns:

        return df

    missing_before = (
        df["brand"]
        .isna()
        .sum()
    )

    df["brand"] = (
        df["brand"]
        .fillna("Unknown")
    )

    print("\n" + "=" * 70)
    print("MISSING BRAND HANDLING")
    print("=" * 70)

    print(
        f"Missing brand values replaced with 'Unknown': "
        f"{missing_before}"
    )

    return df


# ================================================================
# 11. HANDLE MISSING VARIANT
# ================================================================

def handle_missing_variant(df):
    """
    Replace missing variant values with 'Not Specified'.

    We do not attempt to infer a variant from product_name because
    doing so could introduce incorrect information.
    """

    if "variant" not in df.columns:

        return df

    missing_before = (
        df["variant"]
        .isna()
        .sum()
    )

    df["variant"] = (
        df["variant"]
        .fillna("Not Specified")
    )

    print("\n" + "=" * 70)
    print("MISSING VARIANT HANDLING")
    print("=" * 70)

    print(
        f"Missing variant values replaced with "
        f"'Not Specified': {missing_before}"
    )

    return df


# ================================================================
# 12. ANALYZE REMAINING MISSING VALUES
# ================================================================

def analyze_missing_values(df):
    """
    Generate a missing-value report.

    Missing rating and review_count values are intentionally preserved
    because missing does not necessarily mean zero.
    """

    missing_count = (
        df.isna()
        .sum()
    )

    missing_percentage = (
        df.isna()
        .mean()
        .mul(100)
    )

    report = pd.DataFrame({

        "missing_count":
            missing_count,

        "missing_percentage":
            missing_percentage.round(2)

    })

    report = (
        report
        .sort_values(
            "missing_count",
            ascending=False
        )
    )

    print("\n" + "=" * 70)
    print("MISSING VALUE ANALYSIS")
    print("=" * 70)

    print(
        report
    )

    return report


# ================================================================
# 13. REMOVE INVALID PRICE RECORDS
# ================================================================

def remove_invalid_price_records(df):
    """
    Remove records where MRP or selling price is zero/negative.

    Business rule:

        MRP > 0
        Selling Price > 0

    The collected dataset contains 53 observations where both MRP
    and selling price are 0.

    These records cannot be used for competitive pricing analysis
    and are therefore removed.

    The raw dataset remains unchanged.
    """

    if not {
        "mrp",
        "selling_price"
    }.issubset(df.columns):

        return df, 0

    invalid_mask = (

        df["mrp"].isna()
        |
        df["selling_price"].isna()
        |
        (df["mrp"] <= 0)
        |
        (df["selling_price"] <= 0)

    )

    invalid_count = (
        invalid_mask.sum()
    )

    print("\n" + "=" * 70)
    print("INVALID PRICE RECORD REMOVAL")
    print("=" * 70)

    print(
        f"Invalid price records removed: "
        f"{invalid_count}"
    )

    if invalid_count > 0:

        df = (
            df.loc[
                ~invalid_mask
            ]
            .copy()
        )

    return df, invalid_count


# ================================================================
# 14. VALIDATE SELLING PRICE AGAINST MRP
# ================================================================

def validate_price_relationship(df):
    """
    Check whether selling price exceeds MRP.

    This function does NOT remove such records automatically.

    It creates a diagnostic count so that unusual records can be
    investigated.
    """

    if not {
        "mrp",
        "selling_price"
    }.issubset(df.columns):

        return 0

    invalid_relationship = (
        df["selling_price"]
        >
        df["mrp"]
    )

    count = (
        invalid_relationship.sum()
    )

    print("\n" + "=" * 70)
    print("PRICE RELATIONSHIP VALIDATION")
    print("=" * 70)

    print(
        f"Selling price > MRP records: {count}"
    )

    return count


# ================================================================
# 15. RECALCULATE DISCOUNT
# ================================================================

def recalculate_discount(df):
    """
    Recalculate discount percentage from MRP and selling price.

    Formula:

        Discount % =
        ((MRP - Selling Price) / MRP) * 100

    Recalculating the metric ensures consistency across all records.
    """

    if not {
        "mrp",
        "selling_price"
    }.issubset(df.columns):

        return df

    df["discount_pct"] = (

        (
            df["mrp"]
            -
            df["selling_price"]
        )
        /
        df["mrp"]

    ) * 100

    # Round for cleaner storage.
    df["discount_pct"] = (
        df["discount_pct"]
        .round(2)
    )

    return df


# ================================================================
# 16. REMOVE EXACT DUPLICATES
# ================================================================

def remove_exact_duplicates(df):
    """
    Remove completely identical rows.
    """

    before = len(df)

    df = (
        df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    removed = (
        before - len(df)
    )

    print("\n" + "=" * 70)
    print("EXACT DUPLICATE REMOVAL")
    print("=" * 70)

    print(
        f"Exact duplicate rows removed: {removed}"
    )

    return df, removed


# ================================================================
# 17. REMOVE REPEATED SEARCH-QUERY OBSERVATIONS
# ================================================================

def remove_product_search_duplicates(df):
    """
    Remove repeated observations of the same marketplace product
    within the same city.

    BUSINESS GRAIN:

        platform + city + product_id

    Why?

    The same product can be returned for multiple search queries.

    Example:

        Samsung smartphone
        OnePlus smartphone
        Xiaomi smartphone

    may all return the same product ID.

    The product itself is the same. Only the search query differs.

    Therefore, keeping all such records would artificially increase
    the weight of products that appeared in multiple searches.

    We retain the first occurrence and remove subsequent
    search-query duplicates.

    IMPORTANT:
    The city remains part of the key because the same product in
    Bengaluru and Delhi represents separate geographic observations.
    """

    business_key = [
        "platform",
        "city",
        "product_id"
    ]

    missing_key_columns = [
        column
        for column in business_key
        if column not in df.columns
    ]

    if missing_key_columns:

        print(
            "Product-level deduplication skipped."
        )

        print(
            "Missing columns:",
            missing_key_columns
        )

        return df, 0

    before = len(df)

    duplicate_mask = (
        df.duplicated(
            subset=business_key,
            keep="first"
        )
    )

    duplicate_count = (
        duplicate_mask.sum()
    )

    df = (
        df.loc[
            ~duplicate_mask
        ]
        .copy()
        .reset_index(drop=True)
    )

    print("\n" + "=" * 70)
    print("PRODUCT-LEVEL DUPLICATE REMOVAL")
    print("=" * 70)

    print(
        "Business grain:"
    )

    print(
        "platform + city + product_id"
    )

    print(
        f"Repeated search-query observations removed: "
        f"{duplicate_count}"
    )

    print(
        f"Rows before: {before}"
    )

    print(
        f"Rows after : {len(df)}"
    )

    return df, duplicate_count


# ================================================================
# 18. VALIDATE RATINGS
# ================================================================

def validate_ratings(df):
    """
    Validate product ratings.

    Valid range:

        0 <= rating <= 5

    Missing ratings are preserved.
    """

    if "rating" not in df.columns:

        return 0

    invalid_rating_mask = (

        df["rating"].notna()
        &
        (
            (df["rating"] < 0)
            |
            (df["rating"] > 5)
        )

    )

    invalid_count = (
        invalid_rating_mask.sum()
    )

    print("\n" + "=" * 70)
    print("RATING VALIDATION")
    print("=" * 70)

    print(
        f"Invalid rating records: {invalid_count}"
    )

    return invalid_count


# ================================================================
# 19. IDENTIFY PRICE OUTLIERS
# ================================================================

def identify_price_outliers(df):
    """
    Identify potential selling-price outliers using IQR.

    IMPORTANT:

    Outliers are NOT automatically removed.

    A high-priced laptop, television or other premium product may
    be a legitimate business observation.

    Therefore, the outlier is retained and only flagged.
    """

    if "selling_price" not in df.columns:

        return df, 0

    price = (
        df["selling_price"]
        .dropna()
    )

    if price.empty:

        return df, 0

    q1 = price.quantile(
        0.25
    )

    q3 = price.quantile(
        0.75
    )

    iqr = (
        q3 - q1
    )

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    df["selling_price_outlier"] = (

        (df["selling_price"] < lower_bound)
        |
        (df["selling_price"] > upper_bound)

    )

    outlier_count = (
        df["selling_price_outlier"]
        .sum()
    )

    print("\n" + "=" * 70)
    print("PRICE OUTLIER ANALYSIS")
    print("=" * 70)

    print(
        f"Q1             : ₹{q1:,.2f}"
    )

    print(
        f"Q3             : ₹{q3:,.2f}"
    )

    print(
        f"IQR            : ₹{iqr:,.2f}"
    )

    print(
        f"Lower boundary : ₹{lower_bound:,.2f}"
    )

    print(
        f"Upper boundary : ₹{upper_bound:,.2f}"
    )

    print(
        f"Potential outliers: {outlier_count}"
    )

    print(
        "Decision: Outliers are flagged, not removed."
    )

    return df, outlier_count


# ================================================================
# 20. VALIDATE DISCOUNT
# ================================================================

def validate_discount(df):
    """
    Validate calculated discount percentages.

    Valid range:

        0 <= discount <= 100
    """

    if "discount_pct" not in df.columns:

        return 0

    invalid_discount_mask = (

        df["discount_pct"].notna()
        &
        (
            (df["discount_pct"] < 0)
            |
            (df["discount_pct"] > 100)
        )

    )

    invalid_count = (
        invalid_discount_mask.sum()
    )

    print("\n" + "=" * 70)
    print("DISCOUNT VALIDATION")
    print("=" * 70)

    print(
        f"Invalid discount records: {invalid_count}"
    )

    return invalid_count


# ================================================================
# 21. FINAL DATA QUALITY CHECK
# ================================================================

def final_quality_check(df):
    """
    Perform final validation after cleaning.
    """

    print("\n" + "=" * 70)
    print("FINAL DATA QUALITY CHECK")
    print("=" * 70)

    print(
        f"Final rows    : {df.shape[0]}"
    )

    print(
        f"Final columns : {df.shape[1]}"
    )

    print("\nRemaining missing values:")

    print(
        df.isna().sum()
    )

    print("\nFinal data types:")

    print(
        df.dtypes
    )

    # ------------------------------------------------------------
    # Platform distribution.
    # ------------------------------------------------------------

    if "platform" in df.columns:

        print("\nPlatform distribution:")

        print(
            df["platform"]
            .value_counts()
        )

    # ------------------------------------------------------------
    # City distribution.
    # ------------------------------------------------------------

    if "city" in df.columns:

        print("\nCity distribution:")

        print(
            df["city"]
            .value_counts()
        )

    # ------------------------------------------------------------
    # Category distribution.
    # ------------------------------------------------------------

    if "category" in df.columns:

        print("\nCategory distribution:")

        print(
            df["category"]
            .value_counts()
        )

    # ------------------------------------------------------------
    # Platform × City distribution.
    # ------------------------------------------------------------

    if {
        "platform",
        "city"
    }.issubset(df.columns):

        print(
            "\nPlatform × City distribution:"
        )

        print(
            pd.crosstab(
                df["city"],
                df["platform"]
            )
        )


# ================================================================
# 22. CREATE CLEANING REPORT
# ================================================================

def create_cleaning_report(
    initial_rows,
    final_rows,
    completely_missing_columns,
    constant_columns,
    invalid_price_count,
    exact_duplicate_count,
    product_duplicate_count,
    invalid_rating_count,
    outlier_count,
    invalid_discount_count
):
    """
    Create a compact summary of the cleaning process.

    The report is saved as a CSV file so that the transformation
    process can be documented and reproduced.
    """

    report = pd.DataFrame({

        "metric": [

            "Initial rows",
            "Final rows",
            "Rows removed",
            "Completely missing columns removed",
            "Constant columns removed",
            "Invalid price records removed",
            "Exact duplicate rows removed",
            "Repeated product/search observations removed",
            "Invalid rating records",
            "Potential price outliers flagged",
            "Invalid discount records"

        ],

        "value": [

            initial_rows,
            final_rows,
            initial_rows - final_rows,
            ", ".join(
                completely_missing_columns
            ) if completely_missing_columns else "None",

            ", ".join(
                constant_columns
            ) if constant_columns else "None",

            invalid_price_count,
            exact_duplicate_count,
            product_duplicate_count,
            invalid_rating_count,
            outlier_count,
            invalid_discount_count

        ]

    })

    return report


# ================================================================
# 23. SAVE DATA
# ================================================================

def save_data(
    df,
    output_file
):
    """
    Save the cleaned dataset as CSV.
    """

    os.makedirs(
        os.path.dirname(
            output_file
        ),
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False
    )

    print("\n" + "=" * 70)
    print("CLEANED DATASET SAVED")
    print("=" * 70)

    print(
        f"File: {output_file}"
    )

    print(
        f"Rows: {len(df)}"
    )


# ================================================================
# 24. SAVE CLEANING REPORT
# ================================================================

def save_report(
    report,
    report_file
):
    """
    Save the cleaning summary report.
    """

    os.makedirs(
        os.path.dirname(
            report_file
        ),
        exist_ok=True
    )

    report.to_csv(
        report_file,
        index=False
    )

    print("\n" + "=" * 70)
    print("CLEANING REPORT SAVED")
    print("=" * 70)

    print(
        f"File: {report_file}"
    )


# ================================================================
# 25. MAIN CLEANING PIPELINE
# ================================================================

def main():

    # ------------------------------------------------------------
    # STEP 1
    # Load the raw master dataset.
    # ------------------------------------------------------------

    df = load_data(
        INPUT_FILE
    )

    initial_rows = len(df)


    # ------------------------------------------------------------
    # STEP 2
    # Inspect the raw dataset before making changes.
    # ------------------------------------------------------------

    inspect_data(
        df
    )


    # ------------------------------------------------------------
    # STEP 3
    # Standardize column names.
    # ------------------------------------------------------------

    df = standardize_column_names(
        df
    )


    # ------------------------------------------------------------
    # STEP 4
    # Clean textual fields.
    # ------------------------------------------------------------

    df = clean_text_columns(
        df
    )


    # ------------------------------------------------------------
    # STEP 5
    # Convert columns to appropriate data types.
    # ------------------------------------------------------------

    df = convert_data_types(
        df
    )


    # ------------------------------------------------------------
    # STEP 6
    # Remove columns where every value is missing.
    # ------------------------------------------------------------

    completely_missing_columns = [

        column

        for column in df.columns

        if df[column].isna().all()

    ]

    df = remove_completely_missing_columns(
        df
    )


    # ------------------------------------------------------------
    # STEP 7
    # Remove constant/non-informative columns.
    # ------------------------------------------------------------

    constant_columns = [

        column

        for column in df.columns

        if df[column].nunique(
            dropna=False
        ) <= 1

    ]

    df = remove_constant_columns(
        df
    )


    # ------------------------------------------------------------
    # STEP 8
    # Handle missing brand values.
    # ------------------------------------------------------------

    df = handle_missing_brand(
        df
    )


    # ------------------------------------------------------------
    # STEP 9
    # Handle missing variant values.
    # ------------------------------------------------------------

    df = handle_missing_variant(
        df
    )


    # ------------------------------------------------------------
    # STEP 10
    # Analyze remaining missing values.
    # ------------------------------------------------------------

    analyze_missing_values(
        df
    )


    # ------------------------------------------------------------
    # STEP 11
    # Remove invalid zero/negative price records.
    # ------------------------------------------------------------

    df, invalid_price_count = (
        remove_invalid_price_records(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 12
    # Check whether selling price exceeds MRP.
    # ------------------------------------------------------------

    validate_price_relationship(
        df
    )


    # ------------------------------------------------------------
    # STEP 13
    # Recalculate discount percentage.
    # ------------------------------------------------------------

    df = recalculate_discount(
        df
    )


    # ------------------------------------------------------------
    # STEP 14
    # Remove exact duplicate rows.
    # ------------------------------------------------------------

    df, exact_duplicate_count = (
        remove_exact_duplicates(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 15
    # Remove repeated product observations caused by multiple
    # search queries.
    #
    # Business grain:
    # platform + city + product_id
    # ------------------------------------------------------------

    df, product_duplicate_count = (
        remove_product_search_duplicates(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 16
    # Validate ratings.
    # ------------------------------------------------------------

    invalid_rating_count = (
        validate_ratings(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 17
    # Identify potential price outliers.
    #
    # Outliers are retained and flagged.
    # ------------------------------------------------------------

    df, outlier_count = (
        identify_price_outliers(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 18
    # Validate discount percentage.
    # ------------------------------------------------------------

    invalid_discount_count = (
        validate_discount(
            df
        )
    )


    # ------------------------------------------------------------
    # STEP 19
    # Final data-quality validation.
    # ------------------------------------------------------------

    final_quality_check(
        df
    )


    # ------------------------------------------------------------
    # STEP 20
    # Create cleaning report.
    # ------------------------------------------------------------

    report = create_cleaning_report(

        initial_rows=initial_rows,

        final_rows=len(df),

        completely_missing_columns=
            completely_missing_columns,

        constant_columns=
            constant_columns,

        invalid_price_count=
            invalid_price_count,

        exact_duplicate_count=
            exact_duplicate_count,

        product_duplicate_count=
            product_duplicate_count,

        invalid_rating_count=
            invalid_rating_count,

        outlier_count=
            outlier_count,

        invalid_discount_count=
            invalid_discount_count
    )


    # ------------------------------------------------------------
    # STEP 21
    # Save cleaned dataset.
    # ------------------------------------------------------------

    save_data(
        df,
        OUTPUT_FILE
    )


    # ------------------------------------------------------------
    # STEP 22
    # Save cleaning report.
    # ------------------------------------------------------------

    save_report(
        report,
        REPORT_FILE
    )


# ================================================================
# 26. SCRIPT ENTRY POINT
# ================================================================

if __name__ == "__main__":

    main()
