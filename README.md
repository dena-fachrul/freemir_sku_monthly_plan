# SKU Target Data Cleaner Tool

A Streamlit web application designed to automate the cleaning and restructuring of monthly stock target data. It merges SKU details with store-specific targets and unpivots the data into a standardized format for upload.

## Features
- **Header Parsing:** Automatically extracts `Store Code` and `Platform` from complex column headers (e.g., "TTFROS004 - TikTok Electric").
- **Data Unpivoting:** Transforms wide-format store columns (S-AH) into a clean row-based format.
- **Data Enrichment:** Lookups Product Grade based on SKU from a secondary sheet.
- **Smart Filtering:** Automatically removes rows with blank, zero, or text-based target values.

## Input File Structure
1. **Sheet 1 (Main Data):**
   - Header is located at **Row 4** (index 3).
   - **Column F:** SKU.
   - **Columns S to AH:** Store Target Data.
   - **Header Format:** `StoreCode - Platform StoreName`.
2. **Sheet 2 (Product Grade):**
   - **Column A:** SKU.
   - **Column B:** Product Grade.

## How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
