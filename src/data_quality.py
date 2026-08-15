"""
====================================================================
E-COMMERCE DATA QUALITY VALIDATION
====================================================================

PROJECT:
E-Commerce Competitive Pricing & Product Intelligence

PURPOSE:
--------------------------------------------------------------------
This script validates the cleaned E-Commerce dataset before it is
used for Exploratory Data Analysis, SQL analysis and Power BI.

The cleaned dataset was created from product data collected from:

    - Amazon
    - Flipkart

Cities covered:

    - Bengaluru
    - Delhi
    - Mumbai
    - Hyderabad
    - Guwahati

This script DOES NOT modify or clean the dataset.

It only checks whether the cleaned dataset satisfies the expected
business and technical data-quality rules.

QUALITY CHECKS:
--------------------------------------------------------------------
1. File existence
2. Dataset structure
3. Expected columns
4. Missing values
5. Exact duplicates
6. Business-key duplicates
7. Invalid prices
8. Selling price greater than MRP
9. Invalid discount percentages
10. Invalid ratings
11. Invalid review counts
12. Invalid coordinates
13. Invalid timestamps
14. Platform validation
15. City validation
16. Category validation
17. Outlier flag validation
18. Overall data-quality score

OUTPUT:
--------------------------------------------------------------------
data/processed/ecommerce_data_quality_report.csv

IMPORTANT:
--------------------------------------------------------------------
The raw and cleaned datasets are NOT modified by this script.

====================================================================
"""


# ================================================================
# 1. IMPORT LIBRARIES
# ================================================================

import os
import pandas as pd
import numpy as np


# ================================================================
# 2. FILE PATHS
# ================================================================

# Input = cleaned dataset produced by data_cleaning.py.
INPUT_FILE = (
    "data/processed/ecommerce_cleaned.csv"
)

# Output = data quality report.
REPORT_FILE = (
    "data/processed/ecommerce_data_quality_report.csv"
)


# ================================================================
# 3. EXPECTED BUSINESS VALUES
# ================================================================

# Expected marketplaces.
EXPECTED_PLATFORMS = {
    "Amazon",
    "Flipkart"
}

# Expected cities.
EXPECTED_CITIES = {
    "Bengaluru",
    "Delhi",
    "Mumbai",
    "Hyderabad",
    "Guwahati"
}

# Expected categories based on the collected dataset.
EXPECTED_CATEGORIES = {
    "Smartphones",
    "Laptops",
    "Headphones/Earbuds",
    "Smartwatches",
    "Televisions",
    "Home Appliances"
}


# ================================================================
# 4. LOAD CLEANED DATA
# ================================================================

def load_data(file_path):
    """
    Load the cleaned E-Commerce dataset.

    The quality script operates on the output of
    data_cleaning.py.
    """

    print("\n" + "=" * 70)
    print("DATA QUALITY VALIDATION")
    print("=" * 70)

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Cleaned dataset not found: {file_path}"
        )

    df = pd.read_csv(
        file_path
    )

    print(
        f"Dataset loaded successfully: {file_path}"
    )

    print(
        f"Rows    : {df.shape[0]}"
    )

    print(
        f"Columns : {df.shape[1]}"
    )

    return df


# ================================================================
# 5. GENERIC QUALITY CHECK FUNCTION
# ================================================================

def add_check(
    results,
    check_name,
    passed,
    actual_value,
    expected_value,
    severity="ERROR"
):
    """
    Add one quality check result to the report.
    """

    results.append({

        "check_name":
            check_name,

        "status":
            "PASS" if passed else "FAIL",

        "actual_value":
            actual_value,

        "expected_value":
            expected_value,

        "severity":
            severity

    })


# ================================================================
# 6. CHECK DATASET STRUCTURE
# ================================================================

def check_structure(df, results):
    """
    Check whether the cleaned dataset contains the expected
    analytical columns.
    """

    expected_columns = {

        "platform",
        "product_id",
        "product_name",
        "brand",
        "category",
        "variant",
        "mrp",
        "selling_price",
        "discount_pct",
        "rating",
        "review_count",
        "product_url",
        "search_query",
        "city",
        "latitude",
        "longitude",
        "scrape_timestamp",
        "selling_price_outlier"

    }

    actual_columns = set(
        df.columns
    )

    missing_columns = (
        expected_columns
        -
        actual_columns
    )

    unexpected_columns = (
        actual_columns
        -
        expected_columns
    )

    add_check(

        results,

        "Expected columns present",

        len(missing_columns) == 0,

        ", ".join(
            sorted(missing_columns)
        )
        if missing_columns
        else "None",

        "None",

        "ERROR"

    )

    add_check(

        results,

        "No unexpected columns",

        len(unexpected_columns) == 0,

        ", ".join(
            sorted(unexpected_columns)
        )
        if unexpected_columns
        else "None",

        "None",

        "WARNING"

    )


# ================================================================
# 7. CHECK ROW COUNT
# ================================================================

def check_row_count(df, results):
    """
    Make sure the cleaned dataset contains records.
    """

    row_count = len(df)

    add_check(

        results,

        "Dataset contains records",

        row_count > 0,

        row_count,

        "> 0",

        "ERROR"

    )


# ================================================================
# 8. CHECK MISSING VALUES
# ================================================================

def check_missing_values(df, results):
    """
    Check important columns for unexpected missing values.

    Some fields are intentionally allowed to contain missing values:

        - rating
        - review_count

    Brand and variant should already have been handled during cleaning.
    """

    required_columns = [

        "platform",
        "product_id",
        "product_name",
        "brand",
        "category",
        "variant",
        "mrp",
        "selling_price",
        "discount_pct",
        "city"

    ]

    for column in required_columns:

        if column not in df.columns:

            continue

        missing_count = (
            df[column]
            .isna()
            .sum()
        )

        add_check(

            results,

            f"Missing values - {column}",

            missing_count == 0,

            missing_count,

            0,

            "ERROR"

        )

    # ------------------------------------------------------------
    # Rating and review_count are intentionally allowed to be
    # missing.
    # ------------------------------------------------------------

    for column in [
        "rating",
        "review_count"
    ]:

        if column in df.columns:

            missing_count = (
                df[column]
                .isna()
                .sum()
            )

            add_check(

                results,

                f"Missing values allowed - {column}",

                True,

                missing_count,

                "Allowed",

                "INFO"

            )


# ================================================================
# 9. CHECK EXACT DUPLICATES
# ================================================================

def check_exact_duplicates(df, results):
    """
    Check for completely identical rows.
    """

    duplicate_count = (
        df.duplicated()
        .sum()
    )

    add_check(

        results,

        "Exact duplicate rows",

        duplicate_count == 0,

        duplicate_count,

        0,

        "ERROR"

    )


# ================================================================
# 10. CHECK BUSINESS-KEY DUPLICATES
# ================================================================

def check_business_duplicates(df, results):
    """
    Check whether the business grain is unique.

    Business grain:

        platform + city + product_id
    """

    key_columns = [

        "platform",
        "city",
        "product_id"

    ]

    if not all(
        column in df.columns
        for column in key_columns
    ):

        add_check(

            results,

            "Business-key uniqueness",

            False,

            "Required columns missing",

            "Columns available",

            "ERROR"

        )

        return

    duplicate_count = (
        df
        .duplicated(
            subset=key_columns
        )
        .sum()
    )

    add_check(

        results,

        "Business-key uniqueness",

        duplicate_count == 0,

        duplicate_count,

        0,

        "ERROR"

    )


# ================================================================
# 11. CHECK INVALID PRICES
# ================================================================

def check_prices(df, results):
    """
    Validate MRP and selling price.
    """

    invalid_mrp = (
        df["mrp"] <= 0
    ).sum()

    invalid_selling_price = (
        df["selling_price"] <= 0
    ).sum()

    add_check(

        results,

        "MRP greater than zero",

        invalid_mrp == 0,

        invalid_mrp,

        0,

        "ERROR"

    )

    add_check(

        results,

        "Selling price greater than zero",

        invalid_selling_price == 0,

        invalid_selling_price,

        0,

        "ERROR"

    )


# ================================================================
# 12. CHECK PRICE RELATIONSHIP
# ================================================================

def check_price_relationship(df, results):
    """
    Check whether selling price exceeds MRP.
    """

    invalid_count = (
        df["selling_price"]
        >
        df["mrp"]
    ).sum()

    add_check(

        results,

        "Selling price <= MRP",

        invalid_count == 0,

        invalid_count,

        0,

        "ERROR"

    )


# ================================================================
# 13. CHECK DISCOUNT
# ================================================================

def check_discount(df, results):
    """
    Validate discount percentage.
    """

    invalid_discount = (

        (df["discount_pct"] < 0)
        |
        (df["discount_pct"] > 100)

    ).sum()

    add_check(

        results,

        "Discount percentage between 0 and 100",

        invalid_discount == 0,

        invalid_discount,

        0,

        "ERROR"

    )


# ================================================================
# 14. CHECK RATINGS
# ================================================================

def check_ratings(df, results):
    """
    Validate rating values.

    Valid rating range:

        0 to 5
    """

    invalid_rating = (

        df["rating"].notna()
        &
        (
            (df["rating"] < 0)
            |
            (df["rating"] > 5)
        )

    ).sum()

    add_check(

        results,

        "Ratings between 0 and 5",

        invalid_rating == 0,

        invalid_rating,

        0,

        "ERROR"

    )


# ================================================================
# 15. CHECK REVIEW COUNT
# ================================================================

def check_review_count(df, results):
    """
    Review count cannot be negative.

    Missing values are allowed.
    """

    invalid_reviews = (
        df["review_count"]
        .dropna()
        .lt(0)
        .sum()
    )

    add_check(

        results,

        "Review count is non-negative",

        invalid_reviews == 0,

        invalid_reviews,

        0,

        "ERROR"

    )


# ================================================================
# 16. CHECK GEOGRAPHIC COORDINATES
# ================================================================

def check_coordinates(df, results):
    """
    Validate latitude and longitude ranges.

    Latitude:

        -90 to +90

    Longitude:

        -180 to +180
    """

    invalid_latitude = (

        df["latitude"].notna()
        &
        (
            (df["latitude"] < -90)
            |
            (df["latitude"] > 90)
        )

    ).sum()

    invalid_longitude = (

        df["longitude"].notna()
        &
        (
            (df["longitude"] < -180)
            |
            (df["longitude"] > 180)
        )

    ).sum()

    add_check(

        results,

        "Valid latitude",

        invalid_latitude == 0,

        invalid_latitude,

        0,

        "ERROR"

    )

    add_check(

        results,

        "Valid longitude",

        invalid_longitude == 0,

        invalid_longitude,

        0,

        "ERROR"

    )


# ================================================================
# 17. CHECK PLATFORM VALUES
# ================================================================

def check_platforms(df, results):
    """
    Check whether platform values belong to the expected set.
    """

    actual_platforms = set(
        df["platform"]
        .dropna()
        .unique()
    )

    unexpected_platforms = (
        actual_platforms
        -
        EXPECTED_PLATFORMS
    )

    add_check(

        results,

        "Valid platform values",

        len(unexpected_platforms) == 0,

        ", ".join(
            sorted(unexpected_platforms)
        )
        if unexpected_platforms
        else "None",

        "Amazon, Flipkart",

        "ERROR"

    )


# ================================================================
# 18. CHECK CITY VALUES
# ================================================================

def check_cities(df, results):
    """
    Check whether city values belong to the expected project cities.
    """

    actual_cities = set(
        df["city"]
        .dropna()
        .unique()
    )

    unexpected_cities = (
        actual_cities
        -
        EXPECTED_CITIES
    )

    add_check(

        results,

        "Valid city values",

        len(unexpected_cities) == 0,

        ", ".join(
            sorted(unexpected_cities)
        )
        if unexpected_cities
        else "None",

        ", ".join(
            sorted(EXPECTED_CITIES)
        ),

        "ERROR"

    )


# ================================================================
# 19. CHECK CATEGORY VALUES
# ================================================================

def check_categories(df, results):
    """
    Identify categories outside the expected category list.

    This is treated as a warning rather than an error because new
    categories may legitimately appear in future API collections.
    """

    actual_categories = set(
        df["category"]
        .dropna()
        .unique()
    )

    unexpected_categories = (
        actual_categories
        -
        EXPECTED_CATEGORIES
    )

    add_check(

        results,

        "Category validation",

        len(unexpected_categories) == 0,

        ", ".join(
            sorted(unexpected_categories)
        )
        if unexpected_categories
        else "None",

        "Known project categories",

        "WARNING"

    )


# ================================================================
# 20. CHECK OUTLIER FLAG
# ================================================================

def check_outlier_flag(df, results):
    """
    Validate the price-outlier flag.

    The flag should contain only True/False values.
    """

    if "selling_price_outlier" not in df.columns:

        add_check(

            results,

            "Price outlier flag exists",

            False,

            "Column missing",

            "Column exists",

            "ERROR"

        )

        return

    valid_values = (
        df["selling_price_outlier"]
        .dropna()
        .isin(
            [True, False]
        )
        .all()
    )

    add_check(

        results,

        "Price outlier flag valid",

        valid_values,

        "Valid boolean values"
        if valid_values
        else "Invalid values",

        "True / False",

        "ERROR"

    )


# ================================================================
# 21. CHECK TIMESTAMP
# ================================================================

def check_timestamp(df, results):
    """
    Check scrape_timestamp values.

    Invalid/missing timestamps are reported rather than automatically
    removed.
    """

    if "scrape_timestamp" not in df.columns:

        add_check(

            results,

            "Scrape timestamp exists",

            False,

            "Column missing",

            "Column exists",

            "ERROR"

        )

        return

    timestamps = pd.to_datetime(
        df["scrape_timestamp"],
        errors="coerce"
    )

    invalid_timestamp_count = (
        timestamps.isna()
        .sum()
    )

    add_check(

        results,

        "Valid scrape timestamps",

        invalid_timestamp_count == 0,

        invalid_timestamp_count,

        0,

        "WARNING"

    )


# ================================================================
# 22. PLATFORM × CITY COVERAGE CHECK
# ================================================================

def check_platform_city_coverage(
    df,
    results
):
    """
    Check whether every expected city-platform combination exists.

    This does NOT require equal numbers of records.

    It only checks whether observations exist.
    """

    coverage = pd.crosstab(
        df["city"],
        df["platform"]
    )

    missing_combinations = []

    for city in EXPECTED_CITIES:

        for platform in EXPECTED_PLATFORMS:

            if (
                city not in coverage.index
                or
                platform not in coverage.columns
                or
                coverage.loc[
                    city,
                    platform
                ] == 0
            ):

                missing_combinations.append(
                    f"{city} - {platform}"
                )

    add_check(

        results,

        "Platform-city coverage",

        len(missing_combinations) == 0,

        ", ".join(
            missing_combinations
        )
        if missing_combinations
        else "All combinations present",

        "All expected combinations present",

        "WARNING"

    )


# ================================================================
# 23. CREATE QUALITY REPORT
# ================================================================

def create_quality_report(results):
    """
    Convert quality-check results into a DataFrame.
    """

    report = pd.DataFrame(
        results
    )

    return report


# ================================================================
# 24. CALCULATE QUALITY SCORE
# ================================================================

def calculate_quality_score(report):
    """
    Calculate an overall quality score.

    The score is based on ERROR-level checks.

    INFO checks are not included.
    WARNING checks are reported separately.
    """

    error_checks = report[
        report["severity"] == "ERROR"
    ]

    if len(error_checks) == 0:

        return 100.0

    passed_checks = (
        error_checks["status"]
        == "PASS"
    ).sum()

    total_checks = (
        len(error_checks)
    )

    score = (
        passed_checks
        /
        total_checks
    ) * 100

    return round(
        score,
        2
    )


# ================================================================
# 25. PRINT QUALITY SUMMARY
# ================================================================

def print_quality_summary(
    report,
    score
):
    """
    Display a human-readable quality summary.
    """

    total_checks = len(
        report
    )

    passed_checks = (
        report["status"]
        == "PASS"
    ).sum()

    failed_checks = (
        report["status"]
        == "FAIL"
    ).sum()

    print("\n" + "=" * 70)
    print("DATA QUALITY SUMMARY")
    print("=" * 70)

    print(
        f"Total checks  : {total_checks}"
    )

    print(
        f"Passed checks : {passed_checks}"
    )

    print(
        f"Failed checks : {failed_checks}"
    )

    print(
        f"Quality score : {score}%"
    )

    print("\nFailed checks:")

    failed = report[
        report["status"] == "FAIL"
    ]

    if failed.empty:

        print(
            "None"
        )

    else:

        print(
            failed[
                [
                    "check_name",
                    "actual_value",
                    "expected_value",
                    "severity"
                ]
            ].to_string(
                index=False
            )
        )


# ================================================================
# 26. SAVE QUALITY REPORT
# ================================================================

def save_quality_report(
    report,
    score,
    output_file
):
    """
    Save the quality report to CSV.
    """

    os.makedirs(
        os.path.dirname(
            output_file
        ),
        exist_ok=True
    )

    # Add overall score as an additional column.
    report = report.copy()

    report["overall_quality_score"] = (
        score
    )

    report.to_csv(
        output_file,
        index=False
    )

    print("\n" + "=" * 70)
    print("QUALITY REPORT SAVED")
    print("=" * 70)

    print(
        f"File: {output_file}"
    )


# ================================================================
# 27. MAIN FUNCTION
# ================================================================

def main():

    # ------------------------------------------------------------
    # STEP 1
    # Load cleaned dataset.
    # ------------------------------------------------------------

    df = load_data(
        INPUT_FILE
    )

    # ------------------------------------------------------------
    # Store all quality results.
    # ------------------------------------------------------------

    results = []

    # ------------------------------------------------------------
    # STEP 2
    # Structural checks.
    # ------------------------------------------------------------

    check_structure(
        df,
        results
    )

    check_row_count(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 3
    # Missing values.
    # ------------------------------------------------------------

    check_missing_values(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 4
    # Duplicate checks.
    # ------------------------------------------------------------

    check_exact_duplicates(
        df,
        results
    )

    check_business_duplicates(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 5
    # Price validation.
    # ------------------------------------------------------------

    check_prices(
        df,
        results
    )

    check_price_relationship(
        df,
        results
    )

    check_discount(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 6
    # Rating and review validation.
    # ------------------------------------------------------------

    check_ratings(
        df,
        results
    )

    check_review_count(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 7
    # Geographic validation.
    # ------------------------------------------------------------

    check_coordinates(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 8
    # Categorical validation.
    # ------------------------------------------------------------

    check_platforms(
        df,
        results
    )

    check_cities(
        df,
        results
    )

    check_categories(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 9
    # Outlier flag validation.
    # ------------------------------------------------------------

    check_outlier_flag(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 10
    # Timestamp validation.
    # ------------------------------------------------------------

    check_timestamp(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 11
    # Platform-city coverage.
    # ------------------------------------------------------------

    check_platform_city_coverage(
        df,
        results
    )

    # ------------------------------------------------------------
    # STEP 12
    # Create report.
    # ------------------------------------------------------------

    report = create_quality_report(
        results
    )

    # ------------------------------------------------------------
    # STEP 13
    # Calculate score.
    # ------------------------------------------------------------

    score = calculate_quality_score(
        report
    )

    # ------------------------------------------------------------
    # STEP 14
    # Display summary.
    # ------------------------------------------------------------

    print_quality_summary(
        report,
        score
    )

    # ------------------------------------------------------------
    # STEP 15
    # Save report.
    # ------------------------------------------------------------

    save_quality_report(
        report,
        score,
        REPORT_FILE
    )


# ================================================================
# 28. SCRIPT ENTRY POINT
# ================================================================

if __name__ == "__main__":

    main()