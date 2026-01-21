import streamlit as st
import pandas as pd
from datetime import date
import io

# Konfigurasi Halaman
st.set_page_config(
    page_title="SKU Target Cleaner",
    page_icon="🧹",
    layout="wide"
)

# Judul Aplikasi
st.title("🧹 SKU Target Data Cleaner")
st.markdown("""
**Instruksi:**
1. Upload **satu file Excel** yang berisi dua sheet: 
   - `SKU Target` (Data target per toko)
   - `SKU Grade` (Mapping grade produk)
2. Klik tombol **Process Data**.
""")

# --- Sidebar: Input User ---
with st.sidebar:
    st.header("1. Settings")
    
    # Input Tanggal
    target_date = st.date_input("Select Month/Date", value=date(2026, 1, 1))
    formatted_date = target_date.strftime("%Y-%m-%d") # Format: 2026-01-01
    
    # Input Brand
    target_brand = st.text_input("Brand", value="freemir")
    
    st.divider()
    
    st.header("2. Upload File")
    # File Uploader Tunggal
    uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=['xlsx'])

    st.divider()
    
    # Tombol Eksekusi
    run_process = st.button("🚀 Process Data", type="primary")

# --- Fungsi Helper ---

def extract_platform_store(header_str):
    """
    Mendeteksi apakah nama kolom adalah kolom toko.
    Format yang dicari: "KODE - Platform Nama"
    Contoh: "TTFROS004 - TikTok Electric"
    """
    # Pastikan header adalah string dan memiliki pemisah " - "
    if not isinstance(header_str, str) or " - " not in header_str:
        return None, None
        
    try:
        parts = header_str.split(" - ")
        # Bagian kiri: Kode Toko
        store_code = parts[0].strip()
        
        # Bagian kanan: Platform + Nama Toko
        # Kita ambil kata pertama dari bagian kanan sebagai Platform
        right_part = parts[1].strip()
        platform = right_part.split(" ")[0]
        
        return platform, store_code
    except:
        return None, None

def process_excel(file_upload, month_val, brand_val):
    """
    Logika utama: Membaca 1 File Excel dengan 2 Sheet spesifik.
    """
    # 1. Load Excel File
    xls = pd.ExcelFile(file_upload)
    
    # Validasi Nama Sheet
    required_sheets = ['SKU Target', 'SKU Grade']
    for sheet in required_sheets:
        if sheet not in xls.sheet_names:
            return None, f"Sheet '{sheet}' tidak ditemukan dalam file Excel."

    # 2. Baca Sheet "SKU Grade"
    # Header di baris 0 (default)
    df_grade = pd.read_excel(xls, sheet_name='SKU Grade')
    
    # Bersihkan nama kolom grade & buat Dictionary Mapping
    df_grade.columns = [str(c).strip() for c in df_grade.columns]
    # Asumsi: Kolom A (0) = SKU, Kolom B (1) = Grade
    grade_map = dict(zip(df_grade.iloc[:, 0], df_grade.iloc[:, 1]))

    # 3. Baca Sheet "SKU Target"
    # Berdasarkan file 'Input Test', header ada di baris pertama (index 0)
    df_target = pd.read_excel(xls, sheet_name='SKU Target', header=0)
    
    processed_rows = []
    
    # Deteksi Kolom Toko secara Otomatis
    # Kita cari semua kolom yang memiliki pola "Kode - Platform"
    store_columns = []
    for col in df_target.columns:
        plat, code = extract_platform_store(col)
        if plat and code:
            store_columns.append(col)
    
    if not store_columns:
        return None, "Tidak ditemukan kolom Toko dengan format 'Kode - Platform Nama' di sheet SKU Target."

    # 4. Iterasi Baris Data
    for idx, row in df_target.iterrows():
        # Asumsi kolom SKU bernama "SKU" atau berada di kolom pertama (index 0)
        # Kita coba cari kolom bernama 'SKU', jika tidak ada pakai kolom index 0
        if 'SKU' in df_target.columns:
            sku = row['SKU']
        else:
            sku = row.iloc[0]
            
        # --- Filter Data Kotor ---
        # Skip jika SKU kosong
        if pd.isna(sku) or str(sku).strip() == "":
            continue
            
        # Skip baris 'Target', 'Total', dll
        sku_str = str(sku).strip().lower()
        if sku_str in ['target', 'total', 'grand total', 'gmv']:
            continue
            
        # Ambil Grade
        p_grade = grade_map.get(sku, "N/A")
        
        # Loop hanya ke kolom-kolom toko yang valid
        for col_name in store_columns:
            raw_val = row[col_name]
            
            # Cleaning Angka Target
            try:
                target_val = pd.to_numeric(raw_val, errors='coerce')
            except:
                target_val = 0
                
            # Skip jika 0, NaN, atau negatif
            if pd.isna(target_val) or target_val <= 0:
                continue
                
            # Ambil info platform dari nama kolom
            platform, store_code = extract_platform_store(col_name)
            
            # Append data bersih
            processed_rows.append({
                "月份/Month": month_val,
                "品牌/Brand": brand_val,
                "平台/Platform": platform,
                "店铺/Store": store_code,
                "SKU": sku,
                "产品等级/Product grade": p_grade,
                "月目标/Monthly goal": int(target_val)
            })
            
    return pd.DataFrame(processed_rows), None

# --- Eksekusi Utama ---

if run_process:
    if uploaded_file:
        with st.spinner("Processing Excel file..."):
            result_df, error_msg = process_excel(uploaded_file, formatted_date, target_brand)
            
            if error_msg:
                st.error(f"Error: {error_msg}")
            else:
                if not result_df.empty:
                    st.success(f"Berhasil! {len(result_df)} baris data diproses.")
                    
                    st.subheader("Preview Data")
                    st.dataframe(result_df.head(10))
                    
                    # Download Button
                    csv_buffer = result_df.to_csv(index=False).encode('utf-8')
                    filename = f"Cleaned_{target_brand}_{formatted_date}.csv"
                    
                    st.download_button(
                        label="📥 Download Result CSV",
                        data=csv_buffer,
                        file_name=filename,
                        mime="text/csv"
                    )
                else:
                    st.warning("Data kosong setelah diproses. Cek apakah ada nilai target > 0?")
    else:
        st.warning("⚠️ Silakan upload file Excel terlebih dahulu.")
else:
    st.info("👋 Upload file Excel (isi sheet: 'SKU Target' & 'SKU Grade'), lalu klik tombol process.")
