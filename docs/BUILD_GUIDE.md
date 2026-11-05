# Retail Sales Dashboard: Power BI build guide

Portfolio project for data analyst roles. You build one clean data model and a one-page report from 20,550 raw, messy rows.

## Files in this project

| File | What it is |
|---|---|
| `data/retail_sales_raw.csv` | The messy dataset you import (20,550 rows, 15 columns) |
| `powerquery/01_PowerQuery_Sales.m` | Power Query script that cleans it (paste into Advanced Editor) |
| `dax/02_DAX_Measures.dax` | Date table and all measures |
| `data/retail_sales_clean_reference.csv` | What the cleaned table should look like, for checking your work |
| `docs/dashboard_mockup.png` | The target layout (a mock-up, not a Power BI screenshot) |
| `scripts/generate_data.py` | Regenerates the raw dataset (seeded, reproducible) |

## Step 0: Get Power BI Desktop

Power BI Desktop is free but **Windows only**. There is no native Mac version. Options:

- A Windows PC (your own, a friend's, a university or library machine). Download "Power BI Desktop" from the Microsoft Store.
- On a Mac: a Windows virtual machine (for example Parallels) or a hosted cloud PC. Both run the real Desktop app, but they cost money.
- Power BI in the browser (app.powerbi.com) is free to look at but is limited for building: Power Query and modelling features are cut down, and calculated tables like the Date table may not work. I would not rely on it for this project.

## Step 1: Import the data

1. Save `data/retail_sales_raw.csv` to `C:\PowerBI_Project\`.
2. Power BI Desktop > **Get data > Text/CSV** > pick the file > **Transform Data**.

## Step 2: Clean it in Power Query

1. In Power Query Editor: **Home > Advanced Editor**.
2. Delete everything, paste the contents of `powerquery/01_PowerQuery_Sales.m`, and change `FilePath` on the first line if you saved the file elsewhere.
3. Click **Done**, then rename the query to **Sales**.
4. **Close & Apply**.

What the script fixes (good material for your write-up):

| Problem in the raw file | Fix |
|---|---|
| 550 exact duplicate rows | Remove duplicates |
| Dates in 3 formats (`2024-06-17`, `09/12/2025`, `23-Dec-2025`) | Parse as UK day-first |
| Prices stored as text with a pound sign (`£1,299.00`) | Strip symbols, convert to number |
| 60 missing unit prices | Fill from the same product's known price |
| Mixed case, extra spaces, typos (`Electronis`, `Clothng`, `london `) | Trim, proper-case, replace typos |
| Missing segment, city, channel, payment | Replace with "Unknown" |
| Discount as `10` instead of `0.10`, blanks | Divide by 100, blanks become 0 |
| Returned flag as `Y`, `yes`, `TRUE`, `no`, `FALSE` | Standardise to Yes / No |
| 80 invalid quantities (negative, zero, 100+) | Remove rows outside 1 to 20 |
| No revenue or profit columns | Add Revenue, TotalCost, Profit |

## Step 3: Check your row count and totals

Before building anything, confirm the cleaning worked. In Power Query, the Sales table should have **19,920 rows**. After applying, these should match:

| Measure | Expected value |
|---|---|
| Total Revenue | £2,026,713.01 |
| Total Profit | £792,951.13 |
| Profit Margin % | 39.1% |
| Total Orders | 19,920 |
| Average Order Value | £101.74 |
| Unique Customers | 3,780 |
| Return Rate % | 5.8% |

If a number is off, the cleaning step that differs is usually dates (check the culture is `en-GB`) or the duplicate removal. `data/retail_sales_clean_reference.csv` lets you compare row by row.

## Step 4: Date table and measures

1. **Modeling > New table**, paste the `Date = ...` block from `02_DAX_Measures.dax`.
2. **Table tools > Mark as date table** > choose `Date[Date]`.
3. Select `Date[Month]` > **Column tools > Sort by column > Month Number**.
4. **Model view**: drag `Date[Date]` onto `Sales[OrderDate]` (one-to-many, single direction).
5. Create each measure with **Modeling > New measure**, one at a time, pasting from the file.

## Step 5: Build the report page

Use the 16:9 canvas and set a light grey page background. Use one blue (`#2A78D6`) for all bars, and keep colour for the line chart only. Fewer colours looks more professional.

| # | Visual | Fields | Notes |
|---|---|---|---|
| 1 | Text box | "Retail Sales Performance" | Title, top left |
| 2 | Card | `Dashboard Subtitle` | Dynamic date range under the title |
| 3 | Slicers (3) | `Date[Year]`, `Sales[Region]`, `Sales[Category]` | Tile or dropdown style, one row at the top |
| 4 | Cards (6) | Total Revenue, Total Profit, Profit Margin %, Total Orders, Average Order Value, Return Rate % | Add `Revenue YoY %` as a callout on the revenue card |
| 5 | Line chart | X: `Date[Month]`, Y: Total Revenue, Legend: `Date[Year]` | Shows seasonality and growth |
| 6 | Bar chart | Y: `Sales[Category]`, X: Total Revenue | Sort descending |
| 7 | Bar chart | Y: `Sales[Region]`, X: Total Revenue | Sort descending |
| 8 | Bar chart | Y: `Sales[SalesChannel]`, X: Total Revenue | |
| 9 | Bar chart | Y: `Sales[Category]`, X: Profit Margin % | Sort descending |

Finishing touches: turn on data labels, remove gridlines you do not need, align everything to a grid, and give every visual a clear title. Click a bar to check that the other visuals cross-filter.

Stretch goals once the page works:
- Page 2 with a Top 10 products table (Revenue, Profit, Margin %) and a customer segment breakdown.
- Split `Sales` into Products and Customers dimension tables (star schema). Interviewers like this.
- Add a tooltip page or a drill-through from category to product.

## Step 6: What the data says (for your write-up)

These come from the cleaned data, so they should match what you see in Power BI:

1. **Electronics drives a third of revenue but the thinnest margin.** It is 34% of revenue (£691k) at a 25% margin. Beauty (62%) and Clothing (57%) earn far more per pound sold but make up only 8% and 18% of revenue.
2. **Tablets are the single biggest product.** Tablet 10in alone is about £346k, roughly 17% of all revenue.
3. **Revenue is strongly seasonal.** Nov and Dec made up 27% of 2025 revenue.
4. **Growth is healthy.** Jan to Oct 2026 revenue is up 15.7% on the same period of 2025 (£629k vs £544k).
5. **London is the largest region** at £516k, about 25% of revenue, more than double the next region.
6. **Online is the biggest channel** at £957k (47%), ahead of in-store (£685k) and the mobile app (£356k).
7. **5.8% of orders are returned**, which is a data point worth tracking by category.

Suggested recommendation: protect Electronics volume but push higher-margin Beauty and Clothing through the online channel, and plan stock and promotions around the Nov to Dec peak.

## Step 7: Publish it in your portfolio

- Save as `Retail_Sales_Dashboard.pbix`.
- Screenshot the report page (File > Export > PDF also works).
- Put the .pbix, screenshot, the `.m` and `.dax` files, and a short README on GitHub.
- Write 3 to 4 sentences on the problem, your cleaning steps, and your top insights. Post the screenshot on LinkedIn.

## Note on the data

The dataset is synthetic, generated for practice. Say so in your README. Do not present it as real company data.
