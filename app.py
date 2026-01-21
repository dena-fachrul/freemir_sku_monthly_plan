import streamlit as st
import pandas as pd
import io

# Page Configuration
st.set_page_config(
    page_title="SKU Target Cleaner",
    page_icon="🧹",
    layout="wide"
)

# Title and Description
st.title("🧹 SKU Target Data Cleaner")
st.markdown("""
This tool transforms raw stock data into a clean, standardized format for target importing.
**Upload the required CSV files below to get started.**
""")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("1. Global Settings")
    input_month = st.text_input("Month (e.g., 2026-01)", value="2026-01")
    input_brand = st.text_input("Brand (e.g., Freemir)", value="Freemir")
    
    st.header("2. File Uploads")
    uploaded_sheet1 = st.file_uploader("Upload Sheet 1 (Main Data)", type=['csv', 'xlsx'])
    uploaded_sheet2 = st.file_uploader("Upload Sheet 2 (Product Grade)", type=['csv', 'xlsx'])

# --- Helper Functions ---
def load_data(uploaded_file, header_row=0):
    """Helper to load CSV or Excel files."""
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file, header=header_row)
    else:
        return pd.read_excel(uploaded_file, header=header_row)

def extract_platform_store(header_str):
    """
    Parses 'StoreCode - Platform StoreName'
    Example: 'TTFROS004 - TikTok Electric'
    Returns: ('TikTok', 'TTFROS004')
    """
    try:
        if "-" not in header_str:
            return None, None
            
        parts = header_str.split("-")
        store_code = parts[0].strip()
        
        # Second part contains Platform + Name (e.g., "TikTok Electric")
        rest = parts[1].strip()
        # Assume the first word is the Platform
        platform = rest.split(" ")[0]
        
        return platform, store_code
    except Exception:
        return None, None

def process_data(df_main, df_grade, month, brand):
    """Core logic to transform and clean data."""
    
    # 1. Prepare Grade Dictionary (SKU -> Grade)
    # Assuming Sheet 2 has SKU in Col A (0) and Grade in Col B (1)
    # We clean the column names just in case
    df_grade.columns = [str(c).strip() for c in df_grade.columns]
    grade_map = dict(zip(df_grade.iloc[:, 0], df_grade.iloc[:, 1]))

    # 2. Identify Store Columns
    # User specified columns S (index 18) to AH (index 33). 
    # Note: S is the 19th letter, so index 18. AH is 34th, so index 33.
    # We use explicit slicing based on user logic.
    store_columns = df_main.columns[18:34] 

    processed_rows = []

    # 3. Iterate through data
    for idx, row in df_main.iterrows():
        sku = row.iloc[5] # Column F is index 5
        
        # Skip if SKU is missing
        if pd.isna(sku) or str(sku).strip() == "":
            continue

        product_grade = grade_map.get(sku, "N/A") # Lookup Grade

        # Iterate through each store column for this SKU
        for col_name in store_columns:
            raw_goal = row[col_name]
            
            # --- Cleaning Logic ---
            # Convert to numeric, coerce errors to NaN
            goal_value = pd.to_numeric(raw_goal, errors='coerce')
            
            # Skip if NaN, 0, or negative
            if pd.isna(goal_value) or goal_value <= 0:
                continue

            # Extract Store Code and Platform from the Header (col_name)
            platform, store_code = extract_platform_store(col_name)
            
            if platform and store_code:
                processed_rows.append({
                    "月份/Month": month,
                    "品牌/Brand": brand,
                    "平台/Platform": platform,
                    "店铺/Store": store_code,
                    "SKU": sku,
                    "产品等级/Product grade": product_grade,
                    "月目标/Monthly goal": int(goal_value)
                })

    # Create DataFrame
    df_result = pd.DataFrame(processed_rows)
    return df_result

# --- Main Execution ---
if uploaded_sheet1 and uploaded_sheet2:
    try:
        # Load Sheet 1 with header at row 4 (index 3) as specified
        df1 = load_data(uploaded_sheet1, header_row=3)
        # Load Sheet 2 with standard header (index 0)
        df2 = load_data(uploaded_sheet2, header_row=0)

        st.info("Files uploaded successfully. Processing...")
        
        # Process
        result_df = process_data(df1, df2, input_month, input_brand)
        
        # Show Preview
        st.subheader("Data Preview")
        st.dataframe(result_df.head())
        st.write(f"Total Rows Generated: **{len(result_df)}**")

        # Download Button
        csv_buffer = result_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Download Cleaned Data (CSV)",
            data=csv_buffer,
            file_name=f"Cleaned_Target_{input_brand}_{input_month}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
        st.warning("Please check if the file format matches the specified structure (Header at row 4, Store columns S-AH).")

else:
    st.info("Waiting for file uploads...")
