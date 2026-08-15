# E-Commerce Data Collection

## E-Commerce Competitive Pricing & Product Intelligence

This directory documents the data collection process used for the
E-Commerce Competitive Pricing & Product Intelligence project.

The project uses real-world product search data collected from
Amazon and Flipkart across five Indian cities using the
QuickCommerce API.

The collected dataset is used to analyze competitive pricing,
discounts, product availability, product ratings, brand/category
differences, and geographic pricing patterns.

---

## 1. Project Objective

The objective of this project is to understand how product pricing
and marketplace competitiveness vary across Amazon and Flipkart.

The analysis is designed from the perspective of an e-commerce
business/category manager who wants to understand:

- Competitive product pricing
- Discount strategies
- Category-level price differences
- Brand-level price differences
- Product availability
- Customer rating patterns
- City-level pricing differences
- Potential pricing opportunities

---

## 2. Business Problem

E-commerce businesses operate in a highly competitive environment
where customers can compare prices across multiple marketplaces
before making a purchase.

The business problem addressed in this project is:

> How can an e-commerce business use marketplace product data to
> identify pricing gaps, competitive opportunities, discount
> patterns, and availability issues across different cities?

The analysis will answer questions such as:

1. Which marketplace is more price competitive?
2. Which categories have the largest price differences?
3. Which brands show significant pricing differences?
4. Which products have large competitive price gaps?
5. Which marketplace has higher product availability?
6. Which categories offer the highest discounts?
7. Does a higher discount necessarily mean a lower competitive price?
8. How does pricing competitiveness vary across cities?

---

## 3. Data Source

The data was collected using:

**QuickCommerce API**

Documentation:

https://quickcommerceapi.com/docs

QuickCommerce API provides product search and item information
across multiple Indian e-commerce and quick-commerce platforms.

For this project, only the following marketplace platforms were
used:

- Amazon
- Flipkart

The API supports marketplace product search using location
coordinates and search queries.

---

## 4. Data Collection Method

The data collection pipeline was implemented in Python.

The overall process was:

```text
Search Queries
      |
      v
Python
      |
      v
QuickCommerce API
      |
      v
Amazon + Flipkart
      |
      v
JSON Response
      |
      v
Response Parsing
      |
      v
Pandas DataFrame
      |
      v
Data Cleaning
      |
      v
Duplicate Detection
      |
      v
CSV Dataset
```
