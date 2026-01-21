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

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Settings")
    
    # Input Date dengan format khusus YYYY-MM-DD
    # Default ke hari ini, user bisa ganti
    selected_date = st.date_input("Select Date", value=date(2026, 1, 1))
    formatted_month = selected_date.strftime("%Y-%m-%d") # Hasil: 2026-01-01
    
    # Input Brand (Default lowercase 'freemir')
    input_brand = st.text_input("Brand", value="freemir")
    
    st.divider()
    
    st.header("2. Upload Files")
    uploaded_sheet1 = st.file_uploader("Upload Sheet 1 (Main Data)", type=['xlsx', 'csv'])
    uploaded_sheet2 = st.file_uploader("Upload Sheet 2 (Product Grade)", type=['xlsx', 'csv'])

    st.divider()
    
    # Tombol Pelatuk (Trigger)
    process_btn = st.button("🚀 Process Data", type="primary")

# --- Logic Functions ---

def extract_platform_store(header_str):
    """
    Format Header: "KodeToko - Platform NamaToko"
    Contoh: "TTFROS004 - TikTok Electric"
    Output: Platform=TikTok, Store=TTFROS004
    """
    try:
        if "-" not in str(header_str):
            return None, None
            
        parts = str(header_str).split("-")
        # Bagian kiri adalah Kode Toko (misal: TTFROS004)
        store_code = parts[0].strip()
        
        # Bagian kanan adalah Platform + Nama (misal: TikTok Electric)
        right_part = parts[1].strip()
        
        # Ambil kata pertama dari bagian kanan sebagai Platform
        platform = right_part.split(" ")[0]
        
        return platform, store_code
    except Exception:
        return None, None

def process_data(df_main, df_grade, month_val, brand_val):
    # 1. Cleaning Sheet 2 (Grade)
    # Asumsi: Kolom A = SKU, Kolom B = Grade
    df_grade.columns = [str(c).strip() for c in df_grade.columns]
    # Buat dictionary untuk lookup yang cepat
    grade_map = dict(zip(df_grade.iloc[:, 0], df_grade.iloc[:, 1]))

    # 2. Setup Kolom Target (S sampai AH)
    # S adalah kolom ke-19 (index 18)
    # AH adalah kolom ke-34 (index 33)
    # Kita ambil slice index 18 sampai 34 (karena python range exclusive di akhir)
    target_col_indices = list(range(18, 34))
    
    processed_rows = []

    # 3. Iterasi Data Utama
    # Kita iterasi per baris
    for idx, row in df_main.iterrows():
        # Kolom F adalah index 5 (SKU)
        sku = row.iloc[5]
        
        # --- VALIDASI BARIS (PENTING) ---
        # 1. Cek jika SKU kosong/NaN
        if pd.isna(sku) or str(sku).strip() == "":
            continue
            
        # 2. Cek jika baris ini adalah baris "Target" atau "Total" (bukan produk)
        # Seringkali baris 5 berisi total target, kita harus skip
        if str(sku).lower() in ['target', 'total', 'grand total']:
            continue
            
        # Lookup Grade
        product_grade = grade_map.get(sku, "N/A")

        # Loop kolom toko (S - AH)
        for col_idx in target_col_indices:
            # Ambil nama header kolom tersebut untuk ekstrak info toko
            header_name = df_main.columns[col_idx]
            
            # Ambil nilai target (angka)
            raw_val = row.iloc[col_idx]
            
            # Cleaning nilai target
            val = pd.to_numeric(raw_val, errors='coerce')
            
            # Skip jika NaN, 0, atau negatif
            if pd.isna(val) or val <= 0:
                continue
                
            # Ekstrak Info Toko dari Header
            platform, store_code = extract_platform_store(header_name)
            
            # Jika header valid (mengandung "-"), masukkan data
            if platform and store_code:
                processed_rows.append({
                    "月份/Month": month_val,
                    "品牌/Brand": brand_val,
                    "平台/Platform": platform,
                    "店铺/Store": store_code,
                    "SKU": sku,
                    "产品等级/Product grade": product_grade,
                    "月目标/Monthly goal": int(val)
                })
                
    return pd.DataFrame(processed_rows)

# --- Main Execution Flow ---

if process_btn:
    if uploaded_sheet1 and uploaded_sheet2:
        try:
            with st.spinner("Processing data..."):
                # Load Sheet 1: Header di baris 4 (index 3)
                # Ini berarti data SKU mulai dibaca dari baris 5 (index 4)
                df1 = pd.read_excel(uploaded_sheet1, header=3)
                
                # Load Sheet 2: Header standar (baris 1/index 0)
                df2 = pd.read_excel(uploaded_sheet2, header=0)

                # Jalankan Logika
                result_df = process_data(df1, df2, formatted_month, input_brand)
                
                if not result_df.empty:
                    st.success(f"Success! Generated {len(result_df)} rows.")
                    
                    # Tampilkan Preview
                    st.subheader("Preview Result")
                    st.dataframe(result_df.head(10))
                    
                    # Download Button
                    csv_buffer = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Result CSV",
                        data=csv_buffer,
                        file_name=f"Cleaned_{input_brand}_{formatted_month}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No valid data found. Please check: 1. Are columns S-AH containing targets? 2. Is column F containing SKUs?")
                    
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("Please upload both Sheet 1 and Sheet 2 first.")
else:
    # Tampilan awal sebelum tombol ditekan
    st.info("👋 Upload files on the left and click 'Process Data' to start.")
