import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os

# KONFIGURASI HALAMAN
st.set_page_config(
    page_title="PV System Simulator",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded")

HARI_INDO = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
    'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}

BULAN_INDO = {'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
    'April': 'April', 'May': 'Mei', 'June': 'Juni',
    'July': 'Juli', 'August': 'Agustus', 'September': 'September',
    'October': 'Oktober', 'November': 'November', 'December': 'Desember'}

def format_tanggal_indo(dt_obj):
    """Fungsi helper untuk format tanggal Indonesia: 16 September 2024"""
    hari = HARI_INDO[dt_obj.strftime("%A")]
    bulan = BULAN_INDO[dt_obj.strftime("%B")]
    return f"{hari}, {dt_obj.day} {bulan} {dt_obj.year}"

if 'selected_sample' not in st.session_state:
    st.session_state['selected_sample'] = None

@st.cache_data
def load_data(source):
    """Membaca data NASA POWER"""
    try:
        df = pd.read_csv(source, skiprows=10)
        
        required_cols = ['YEAR', 'MO', 'DY', 'HR', 'ALLSKY_SFC_SW_DWN', 'T2M']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Format data salah! Pastikan file memiliki kolom: {required_cols}")
            return None

        df['Datetime'] = pd.to_datetime(df[['YEAR', 'MO', 'DY', 'HR']].astype(str).agg('-'.join, axis=1), format='%Y-%m-%d-%H')
        df.set_index('Datetime', inplace=True)

        df.replace(-999, np.nan, inplace=True)
        df.interpolate(method='linear', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
        return None

def calculate_energy(df, system_capacity_kwp, derating, temp_coeff, noct):
    """Inti Simulasi Fisika PV"""
    df_calc = df.copy()
    
    # 1. Hitung Temperatur Sel
    df_calc['T_cell'] = df_calc['T2M'] + (df_calc['ALLSKY_SFC_SW_DWN'] / 800) * (noct - 20)

    # 2. Faktor Koreksi Suhu
    df_calc['Temp_Correction'] = 1 + temp_coeff * (df_calc['T_cell'] - 25)

    # 3. Hitung Output Daya (kW)
    df_calc['PV_Output_kW'] = system_capacity_kwp * (df_calc['ALLSKY_SFC_SW_DWN'] / 1000) * df_calc['Temp_Correction'] * derating
    
    # Clip nilai negatif
    df_calc['PV_Output_kW'] = df_calc['PV_Output_kW'].clip(lower=0)
    
    return df_calc

# Side bar
with st.sidebar:
    st.image("https://content.app-sources.com/s/04675041793067539/uploads/webpics/REBUILD_Presentationblog-5957894.webp?format=webp", width=300)
    st.title("🎛️ Konfigurasi Sistem")
    st.markdown("---")
    
    st.subheader("1. Input Data")
    uploaded_file = st.file_uploader("Unggah File CSV (NASA POWER)", type=['csv'])
    
    if uploaded_file is not None:
        st.session_state['selected_sample'] = None
    
    st.subheader("2. Spesifikasi PV")
    
    sys_cap_wp = st.number_input(
        "Kapasitas Panel (Watt-peak / Wp)", 
        min_value=10,   
        value=5000,      
        step=50,        
        help="Masukkan angka dalam Watt. Contoh: 1000")
    
    sys_cap_kwp = sys_cap_wp / 1000
    
    with st.expander("Parameter Lanjutan (Engineering)"):
        derating = st.slider("Derating Factor (Efisiensi Sistem)", 0.5, 1.0, 0.80, help="Efisiensi Inverter, Kabel, Debu, dll.")
        temp_coeff_pct = st.number_input("Koefisien Temperatur (%/°C)", value=-0.40, step=0.01)
        temp_coeff = temp_coeff_pct / 100
        noct = st.number_input("NOCT (°C)", value=45.0, step=1.0, help="Nominal Operating Cell Temperature")

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: small;'>
            <a href='https://www.instagram.com/rqwnmrgnn' target='_blank' style='text-decoration: none; color: gray;'>
                Dibuat oleh Muhammad Raqwan dengan ❤️
            </a>
        </div>
        """,
        unsafe_allow_html=True)

# Halaman Utama
st.title("☀️ Simulator Energi Listrik Surya (PV)")
st.markdown(f"""
Aplikasi ini mensimulasikan potensi produksi energi listrik dari sistem PLTS Atap berkapasitas **{sys_cap_wp} Wp** berdasarkan data meteorologi **NASA POWER**.
""")

# Prosesing FIle
file_to_process = None
location_name = "Data Unggahan User"

if uploaded_file is not None:
    file_to_process = uploaded_file
    location_name = uploaded_file.name
elif st.session_state['selected_sample'] is not None:
    file_to_process = st.session_state['selected_sample']
    location_name = st.session_state['selected_sample'].replace(".csv", "")

# ------------------------------------------------

if file_to_process is not None:
    with st.spinner(f'Sedang memproses data: {location_name}...'):
        df = load_data(file_to_process)

    if df is not None:
        if st.session_state['selected_sample']:
            st.info(f"ℹ️ Sedang menjalankan simulasi menggunakan data sampel: **{location_name}**")
            if st.button("❌ Tutup Data Sampel"):
                st.session_state['selected_sample'] = None
                st.rerun()

        # Simulasi
        df_result = calculate_energy(df, sys_cap_kwp, derating, temp_coeff, noct)
        
        # Agregasi Data
        total_energy_kwh = df_result['PV_Output_kW'].sum()
        monthly_energy = df_result['PV_Output_kW'].resample('M').sum()
        daily_energy = df_result['PV_Output_kW'].resample('D').sum()
        avg_daily_energy = daily_energy.mean()
        
        # Specific Yield
        specific_yield = total_energy_kwh / sys_cap_kwp
        
        # Hitung Penghematan (asumsi biaya listrik 1444/kWh)
        estimasi_rupiah = total_energy_kwh * 1444
        rupiah_text = f"Rp {int(estimasi_rupiah):,}".replace(",", ".")
        
        # MENCARI PUNCAK TERTINGGI
        idx_max = df_result['PV_Output_kW'].idxmax()  
        val_max_kw = df_result.loc[idx_max, 'PV_Output_kW'] 
        
        puncak_jam = idx_max.hour
        nama_hari_inggris = idx_max.strftime("%A")
        nama_bulan_inggris = idx_max.strftime("%B")
        
        puncak_hari = HARI_INDO[nama_hari_inggris]      
        puncak_tgl = idx_max.strftime("%d")             
        puncak_bln = BULAN_INDO[nama_bulan_inggris]     
        puncak_thn = idx_max.year                       
        
        df_best_day = df_result[df_result.index.date == idx_max.date()]

        # DASHBOARD HASIL 
        st.success("✅ Simulasi Selesai!")
        
        # A. Key Metrics
        st.markdown("### 📊 Ringkasan Performa Tahunan")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if total_energy_kwh < 1000:
                st.metric("Total Produksi Energi", f"{total_energy_kwh:,.2f} kWh", delta="Per Tahun")
            else:
                st.metric("Total Produksi Energi", f"{total_energy_kwh/1000:,.2f} MWh", delta="Per Tahun")
                
        with col2:
            st.metric("Specific Yield", f"{specific_yield:,.0f} kWh/kWp", help="Indikator produktivitas sistem (Standar bagus: >1300)")
            
        with col3:
            st.metric("Potensi Hemat", rupiah_text, help="Estimasi penghematan tagihan listrik (TDL Rp 1.444/kWh)")
            
        with col4:
            co2 = total_energy_kwh * 0.85 
            if co2 < 1000:
                st.metric("Reduksi CO2", f"{co2:,.2f} kg", delta_color="inverse")
            else:
                st.metric("Reduksi CO2", f"{co2/1000:,.2f} Ton", delta_color="inverse")

        st.markdown("---")

        # B. Grafik Bulanan & Harian Tertinggi
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("📅 Produksi Bulanan (kWh)")
            
            bulan_labels = [BULAN_INDO[d.strftime('%B')] for d in monthly_energy.index]
            
            fig_monthly = px.bar(
                x=bulan_labels, 
                y=monthly_energy.values,
                labels={'x': 'Bulan', 'y': 'Energi (kWh)'},
                color=monthly_energy.values,
                color_continuous_scale='Viridis')
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)

        with col_chart2:
            st.subheader(f"⚡ Profil Daya Tertinggi ({puncak_tgl} {puncak_bln} {puncak_thn})")
            
            st.info(f"**Puncak Tertinggi:** Jam **{puncak_jam}:00**, Hari **{puncak_hari}**, Tanggal **{puncak_tgl} {puncak_bln}**.")
            
            y_watt_peak = df_best_day['PV_Output_kW'] * 1000
            
            fig_hourly = px.area(
                x=df_best_day.index.hour, 
                y=y_watt_peak,
                labels={'x': 'Jam (LST)', 'y': 'Daya Output (Watt)'},
                color_discrete_sequence=['#FFC107'])
            
            fig_hourly.add_annotation(
                x=puncak_jam,
                y=val_max_kw * 1000,
                text=f"Max: {val_max_kw*1000:.1f} W",
                showarrow=True,
                arrowhead=1)
            
            fig_hourly.add_trace(go.Scatter(x=df_best_day.index.hour, y=y_watt_peak, mode='lines', line=dict(color='orange'), name='Output Harian'))
            fig_hourly.update_layout(showlegend=False)
            st.plotly_chart(fig_hourly, use_container_width=True)

        # C. Tren Harian
        st.markdown("---")
        st.subheader("📆 Tren Produksi Harian")
        
        col_daily_metric, col_daily_chart = st.columns([1, 3])
        
        with col_daily_metric:
            st.metric(
                label="Rata-rata Energi Harian",
                value=f"{avg_daily_energy:.2f} kWh",
                help="Nilai rata-rata dari seluruh produksi harian selama setahun.")
            st.caption(f"Setara dengan pemakaian lampu LED 10 Watt selama {int((avg_daily_energy*1000)/10)} jam.")

        with col_daily_chart:
            fig_daily = px.line(
                daily_energy, 
                y='PV_Output_kW',
                labels={'Datetime': 'Tanggal', 'PV_Output_kW': 'Energi (kWh)'},
                title="Produksi Listrik per Hari (kWh)")
            fig_daily.update_traces(line_color='#2ECC71')
            st.plotly_chart(fig_daily, use_container_width=True)

        # D. Cek Produksi Spesifik
        st.markdown("---")
        st.subheader("🔍 Cek Produksi Spesifik per Tanggal")
        st.write("Ingin tahu berapa energi yang dihasilkan pada tanggal tertentu? Silakan pilih tanggal di bawah ini.")
        
        min_date = df_result.index.min().date()
        max_date = df_result.index.max().date()
        default_val = idx_max.date() 
        
        col_input_date, col_res_date = st.columns([1, 3])
        
        with col_input_date:
            selected_date = st.date_input("Pilih Tanggal:", value=default_val, min_value=min_date, max_value=max_date)
            
        df_selected = df_result[df_result.index.date == selected_date]
        
        with col_res_date:
            if not df_selected.empty:
                daily_total_kwh = df_selected['PV_Output_kW'].sum()
                peak_watt_day = df_selected['PV_Output_kW'].max() * 1000
                
                tgl_indo_str = f"{selected_date.day} {BULAN_INDO[selected_date.strftime('%B')]} {selected_date.year}"
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(f"Total Energi ({selected_date.strftime('%d')} {BULAN_INDO[selected_date.strftime('%B')]})", f"{daily_total_kwh:.2f} kWh")
                with c2:
                    st.metric("Daya Puncak Sesaat", f"{peak_watt_day:.1f} Watt")
                
                fig_sel_day = px.area(
                    x=df_selected.index.hour,
                    y=df_selected['PV_Output_kW'] * 1000,
                    labels={'x': 'Jam (LST)', 'y': 'Daya (Watt)'},
                    title=f"Profil Produksi Daya pada {tgl_indo_str}",
                    color_discrete_sequence=['#3498DB'] )
                st.plotly_chart(fig_sel_day, use_container_width=True)
            else:
                st.warning("Data tidak tersedia untuk tanggal yang dipilih.")

        # E. Scatter & Download
        st.markdown("---")
        st.markdown("### 🔬 Analisis Losses Akibat Temperatur")
        st.info("Grafik scatter di bawah memvisualisasikan bagaimana efisiensi panel menurun (warna merah) saat temperatur sel naik akibat radiasi matahari yang tinggi.")
        
        fig_scatter = px.scatter(
            df_result, 
            x='ALLSKY_SFC_SW_DWN', 
            y='T_cell', 
            color='Temp_Correction',
            title='Hubungan Irradiance vs Temperatur Sel vs Faktor Koreksi',
            labels={
                'ALLSKY_SFC_SW_DWN': 'Irradiance (W/m²)', 
                'T_cell': 'Temperatur Sel (°C)',
                'Temp_Correction': 'Faktor Efisiensi Suhu'},
            color_continuous_scale='RdBu')
        st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("📥 Unduh Laporan Lengkap"):
            st.dataframe(df_result[['ALLSKY_SFC_SW_DWN', 'T2M', 'T_cell', 'PV_Output_kW']].head())
            
            csv = df_result.to_csv().encode('utf-8')
            st.download_button(
                label="Unduh CSV",
                data=csv,
                file_name='laporan_simulasi_pv.csv',
                mime='text/csv',)

else:
    # TAMPILAN AWAL
    st.warning("⚠️ Silakan unggah file CSV dari NASA POWER di sidebar.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Langkah Penggunaan:**
        1. Akses data dari [NASA POWER Viewer](https://power.larc.nasa.gov/data-access-viewer/).
        2. Tentukan titik yang akan di analisis
        3. Pilih bagian single point di sidebar kiri
        4. Pada bagian **User Community** pilih **Renewable Energy**.
        5. Lalu pada bagian **Temporal Level** Pilih **Hourly**.
        6. Pilih Tanggal yang diinginkan (disarankan 1 tahun penuh).
        7. Parameter wajib: `All Sky Surface Shortwave Downward Irradiance` & `Temperature at 2 Meters`.
        8. Pilih format **CSV**. Lalu Klik **Submit** untuk mengunduh.
        9. Unggah file CSV di sidebar kiri aplikasi ini.
        10. Atur kapasitas/spesifikasi PV di sidebar kiri.""")
        
    # DATA SAMPEL 
    st.markdown("---")
    st.subheader("🧪 Atau Coba Langsung (Data Sampel)")
    st.write("Klik salah satu lokasi di bawah untuk menjalankan simulasi tanpa perlu mengunduh data:")

    col_s1, col_s2, col_s3 = st.columns(3)

    file_bandung = "Bangbayang Selatan, Bandung, Indonesia.csv"
    file_barcelona = "Camp Nou, Barcelona, Spain.csv"
    file_manchester = "Old Trafford, Manchester, England.csv"

    with col_s1:
        if st.button("🇮🇩 Bandung, Indonesia", use_container_width=True):
            if os.path.exists(file_bandung):
                st.session_state['selected_sample'] = file_bandung
                st.rerun()
            else:
                st.error(f"File '{file_bandung}' tidak ditemukan!")

    with col_s2:
        if st.button("🇪🇸 Barcelona, Spain", use_container_width=True):
            if os.path.exists(file_barcelona):
                st.session_state['selected_sample'] = file_barcelona
                st.rerun()
            else:
                st.error(f"File '{file_barcelona}' tidak ditemukan!")

    with col_s3:
        if st.button("🇬🇧 Manchester, UK", use_container_width=True):
            if os.path.exists(file_manchester):
                st.session_state['selected_sample'] = file_manchester
                st.rerun()
            else:
                st.error(f"File '{file_manchester}' tidak ditemukan!")