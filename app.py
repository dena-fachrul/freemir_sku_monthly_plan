import streamlit as st
import pandas as pd
from datetime import date

# Page Configuration
st.set_page_config(
    page_title="SKU Target Cleaner",
    page_icon="🧹",
    layout="wide"
)

# Title
st.title("🧹 SKU Target Data Cleaner")
st.markdown("Upload data stock dan grade, atur parameter, lalu klik tombol proses.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Settings")
    
    # Input Date: Default 1 Jan 2026, Format output string YYYY-MM-DD
    target_date = st.date_input("Select Month/Date", value=date(2026, 1, 1))
    formatted_date = target_date.strftime("%Y-%m-%d") # Output: 2026-01-01
    
    # Input Brand: Default 'freemir' (lowercase)
    target_brand = st.text_input("Brand", value="freemir")
    
    st.divider()
    
    st.header("2. Upload Files")
    # File Uploader
    uploaded_sheet1 = st.file_uploader("Upload Sheet 1 (Main Data)", type=['xlsx', 'csv'])
    uploaded_sheet2 = st.file_uploader("Upload Sheet 2 (Product Grade)", type=['xlsx', 'csv'])

    st.divider()
    
    # TOMBOL PROSES (Trigger)
    # Proses hanya berjalan jika tombol ini ditekan
    run_process = st.button("🚀 Process Data", type="primary")

# --- Helper Functions ---

def extract_platform_store(header_str):
    """
    Memecah Header: "TTFROS004 - TikTok Electric"
    Menjadi: Platform="TikTok", Store="TTFROS004"
    """
    try:
        if "-" not in str(header_str):
            return None, None
            
        parts = str(header_str).split("-")
        store_code = parts[0].strip() # Kiri: Kode Toko
        
        # Kanan: "TikTok Electric" -> Ambil kata pertama saja
        rest_part = parts[1].strip()
        platform = rest_part.split(" ")[0]
        
        return platform, store_code
    except Exception:
        return None, None

def clean_data(df_main, df_grade, month_val, brand_val):
    """
    Logika utama pembersihan data.
    """
    # 1. Persiapkan Data Grade (Sheet 2)
    # Pastikan nama kolom bersih
    df_grade.columns = [str(c).strip() for c in df_grade.columns]
    # Buat Dictionary: {SKU: Grade} (Kolom A dan B)
    grade_map = dict(zip(df_grade.iloc[:, 0], df_grade.iloc[:, 1]))

    # 2. Tentukan Area Kolom Toko (Sheet 1)
    # User info: Kolom S (index 18) sampai AH (index 33)
    # Range python bersifat exclusive di akhir, jadi 18 sampai 34
    store_col_indices = list(range(18, 34)) 

    processed_rows = []

    # 3. Iterasi Baris Data Utama
    for idx, row in df_main.iterrows():
        # Ambil SKU dari Kolom F (Index 5)
        sku = row.iloc[5]
        
        # --- FILTERING PENTING ---
        # 1. Skip jika SKU kosong/NaN
        if pd.isna(sku) or str(sku).strip() == "":
            continue
            
        # 2. Skip jika baris ini adalah baris "Target" atau "Total"
        # (Biasanya baris ke-5 berisi total target, bukan SKU produk)
        sku_str = str(sku).strip().lower()
        if sku_str in ['target', 'grand total', 'total', 'sku']: 
            continue

        # Lookup Grade
        p_grade = grade_map.get(sku, "N/A") # Default N/A jika tidak ketemu

        # Loop ke setiap kolom toko (S s/d AH)
        for col_idx in store_col_indices:
            # Header kolom ini (misal: "TTFROS004 - TikTok Electric")
            col_header = df_main.columns[col_idx]
            
            # Nilai Target
            raw_target = row.iloc[col_idx]
            
            # Konversi ke angka
            try:
                target_val = pd.to_numeric(raw_target, errors='coerce')
            except:
                target_val = 0
            
            # Hanya ambil jika valid (> 0)
            if pd.isna(target_val) or target_val <= 0:
                continue

            # Ekstrak Platform & Store dari Header
            platform, store_code = extract_platform_store(col_header)
            
            if platform and store_code:
                processed_rows.append({
                    "月份/Month": month_val,
                    "品牌/Brand": brand_val,
                    "平台/Platform": platform,
                    "店铺/Store": store_code,
                    "SKU": sku,
                    "产品等级/Product grade": p_grade,
                    "月目标/Monthly goal": int(target_val)
                })

    return pd.DataFrame(processed_rows)

# --- Main Execution ---

if run_process:
    if uploaded_sheet1 and uploaded_sheet2:
        try:
            with st.spinner(f"Processing data for {formatted_date}..."):
                # Load Sheet 1: Header di baris 4 (index 3)
                # Artinya data SKU dibaca mulai dari baris 5 (index 4)
                df1 = pd.read_excel(uploaded_sheet1, header=3)
                
                # Load Sheet 2: Header standar baris 1 (index 0)
                df2 = pd.read_excel(uploaded_sheet2, header=0)

                # Jalankan Cleaning
                result_df = clean_data(df1, df2, formatted_date, target_brand)
                
                # Tampilkan Hasil
                st.success(f"Done! Processed {len(result_df)} rows.")
                
                st.subheader("Preview Data")
                st.dataframe(result_df.head(10))
                
                # Download Button
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                filename = f"Cleaned_{target_brand}_{formatted_date}.csv"
                
                st.download_button(
                    label="📥 Download Result CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error processing files: {e}")
            st.warning("Hint: Pastikan file Sheet 1 memiliki header di baris ke-4 dan kolom target dari S hingga AH.")
    else:
        st.warning("⚠️ Please upload both files first.")
else:
    st.info("👋 Upload your files and click 'Process Data' to start.")
