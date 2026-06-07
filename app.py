import streamlit as st
import pandas as pd
import folium
import json

from streamlit_folium import folium_static
import plotly.express as px

st.set_page_config(
    page_title="Dashboard DBD Kota Bogor 2025",
    page_icon="🦟",
    layout="wide"
)

st.title("🦟 Dashboard Pemetaan dan Analisis Spasial")
st.subheader("Sebaran Kasus Demam Berdarah Dengue (DBD) Kota Bogor 2025")
st.markdown("---")

@st.cache_data
def load_data():
    return pd.read_csv("data/dbd_bogor_2025.csv")

@st.cache_data
def load_geojson():
    with open(
        "assets/id3271_kota_bogor.geojson",
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)

df_kel = load_data()
geojson_data = load_geojson()

df_kel["kelurahan"] = df_kel["kelurahan"].astype(str).str.strip()
df_kel["kecamatan"] = df_kel["kecamatan"].astype(str).str.strip()

for feature in geojson_data["features"]:
    feature["properties"]["village"] = str(feature["properties"]["village"]).strip()

geojson_kel = {f["properties"]["village"] for f in geojson_data["features"]}
csv_kel = set(df_kel["kelurahan"])
missing = csv_kel - geojson_kel

if missing:
    st.error(f"Kelurahan tidak ditemukan di GeoJSON: {', '.join(sorted(missing))}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Kasus DBD 2025", int(df_kel["jumlah_kasus_2025"].sum()))

with col2:
    st.metric("Jumlah Kelurahan", len(df_kel))

with col3:
    st.metric("Kasus Tertinggi", int(df_kel["jumlah_kasus_2025"].max()))

with col4:
    kel_tertinggi = df_kel.loc[df_kel["jumlah_kasus_2025"].idxmax(), "kelurahan"]
    st.metric("Kelurahan Tertinggi", kel_tertinggi)

st.markdown("---")

col_kiri, col_kanan = st.columns([1.4, 1])

with col_kiri:
    st.subheader("🗺️ Peta Sebaran DBD per Kelurahan")

    m = folium.Map(
        location=[-6.595, 106.816],
        zoom_start=12,
        tiles="CartoDB positron"
    )

    folium.Choropleth(
        geo_data=geojson_data,
        data=df_kel,
        columns=["kelurahan", "jumlah_kasus_2025"],
        key_on="feature.properties.village",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.5,
        line_color="black",
        legend_name="Jumlah Kasus DBD 2025",
        nan_fill_color="lightgray",
        highlight=True
    ).add_to(m)

    folium.GeoJson(
        geojson_data,
        style_function=lambda x: {
            "fillOpacity": 0,
            "weight": 1,
            "color": "#333333"
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["village", "district"],
            aliases=["Kelurahan:", "Kecamatan:"],
            sticky=True
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)
    folium_static(m, width=800, height=550)
    kol1, kol2, kol3, kol4, kol5 = st.columns(5)

    with kol1:
        st.markdown(
            """
            <div style='background-color:#ffffb2; padding:8px; 
            border-radius:6px; text-align:center; border:1px solid #ccc;'>
                <b>🟡 Kuning</b><br>
                <small>1 – 5 kasus</small><br>
                <small>Risiko Rendah</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kol2:
        st.markdown(
            """
            <div style='background-color:#fecc5c; padding:8px; 
            border-radius:6px; text-align:center; border:1px solid #ccc;'>
                <b>🟠 Kuning Tua</b><br>
                <small>6 – 10 kasus</small><br>
                <small>Risiko Sedang</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kol3:
        st.markdown(
            """
            <div style='background-color:#fd8d3c; padding:8px; 
            border-radius:6px; text-align:center; border:1px solid #ccc;'>
                <b>🟧 Orange</b><br>
                <small>11 – 15 kasus</small><br>
                <small>Risiko Tinggi</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kol4:
        st.markdown(
            """
            <div style='background-color:#f03b20; padding:8px; 
            border-radius:6px; text-align:center; border:1px solid #ccc; color:white;'>
                <b>🔴 Merah</b><br>
                <small>16 – 20 kasus</small><br>
                <small>Risiko Sangat Tinggi</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kol5:
        st.markdown(
            """
            <div style='background-color:#bd0026; padding:8px; 
            border-radius:6px; text-align:center; border:1px solid #ccc; color:white;'>
                <b>🔴 Merah Tua</b><br>
                <small>21 – 24 kasus</small><br>
                <small>Risiko Kritis</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Arahkan kursor ke wilayah peta untuk melihat nama kelurahan dan kecamatan beserta jumlah kasusnya.")

with col_kanan:
    st.subheader("📊 Total Kasus per Kecamatan")

    df_kecamatan = (
        df_kel
        .groupby("kecamatan", as_index=False)["jumlah_kasus_2025"]
        .sum()
        .sort_values("jumlah_kasus_2025", ascending=False)
    )

    fig = px.bar(
        df_kecamatan,
        x="kecamatan",
        y="jumlah_kasus_2025",
        color="jumlah_kasus_2025",
        color_continuous_scale="YlOrRd",
        text="jumlah_kasus_2025"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=500,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Kecamatan",
        yaxis_title="Jumlah Kasus"
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("📈 Top 15 Kelurahan dengan Kasus DBD Tertinggi")

df_top15 = df_kel.nlargest(15, "jumlah_kasus_2025")

fig_top = px.bar(
    df_top15,
    x="kelurahan",
    y="jumlah_kasus_2025",
    color="kecamatan",
    text="jumlah_kasus_2025",
    labels={
        "kelurahan": "Kelurahan",
        "jumlah_kasus_2025": "Jumlah Kasus",
        "kecamatan": "Kecamatan"
    }
)

fig_top.update_traces(textposition="outside")
fig_top.update_layout(height=450)
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

st.subheader("📋 Data Kelurahan")

col_f1, col_f2 = st.columns(2)

with col_f1:
    kecamatan_list = ["Semua"] + sorted(df_kel["kecamatan"].unique().tolist())
    filter_kec = st.selectbox("Filter Kecamatan", kecamatan_list)

with col_f2:
    filter_min, filter_max = st.slider(
        "Filter Jumlah Kasus",
        min_value=int(df_kel["jumlah_kasus_2025"].min()),
        max_value=int(df_kel["jumlah_kasus_2025"].max()),
        value=(int(df_kel["jumlah_kasus_2025"].min()), int(df_kel["jumlah_kasus_2025"].max()))
    )

df_filtered = df_kel.copy()

if filter_kec != "Semua":
    df_filtered = df_filtered[df_filtered["kecamatan"] == filter_kec]

df_filtered = df_filtered[
    (df_filtered["jumlah_kasus_2025"] >= filter_min) &
    (df_filtered["jumlah_kasus_2025"] <= filter_max)
]

df_show = df_filtered.sort_values("jumlah_kasus_2025", ascending=False).reset_index(drop=True)
df_show.index += 1

st.dataframe(df_show, use_container_width=True)

st.markdown("---")
st.caption("📌 Sumber Data: Dinas Kesehatan Kota Bogor Tahun 2025")