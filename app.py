import streamlit as st
import pandas as pd
import folium
import json
import re

from streamlit_folium import st_folium
import plotly.express as px

st.set_page_config(
    page_title="Dashboard DBD Kabupaten Bogor",
    page_icon="🦟",
    layout="wide"
)

st.title("🦟 Dashboard Pemetaan dan Analisis Spasial")
st.subheader("Sebaran Kasus Demam Berdarah Dengue (DBD) Kabupaten Bogor")
st.markdown("---")


@st.cache_data
def load_data():
    return pd.read_csv("data/dbd_kabbogor.csv")


@st.cache_data
def load_geojson():
    with open("assets/id3201_bogor_kecamatan.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


df = load_data()
geojson_data = load_geojson()

df["kecamatan"] = df["kecamatan"].astype(str).str.strip()

for feature in geojson_data["features"]:
    feature["properties"]["district"] = str(
        feature["properties"]["district"]
    ).strip()

tahun_list = sorted(df["tahun"].unique())

selected_year = st.selectbox(
    "Pilih Tahun",
    tahun_list,
    index=len(tahun_list) - 1
)

df_year = df[df["tahun"] == selected_year].copy()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Kasus DBD", int(df_year["jumlah_kasus"].sum()))

with col2:
    st.metric("Jumlah Kecamatan", len(df_year))

with col3:
    st.metric("Kasus Tertinggi", int(df_year["jumlah_kasus"].max()))

with col4:
    kec_tertinggi = df_year.loc[df_year["jumlah_kasus"].idxmax(), "kecamatan"]
    st.metric("Kecamatan Tertinggi", kec_tertinggi)

st.markdown("---")

kasus_dict = dict(zip(df_year["kecamatan"], df_year["jumlah_kasus"]))

for feature in geojson_data["features"]:
    nama_kec = feature["properties"]["district"]
    feature["properties"]["jumlah_kasus"] = int(kasus_dict.get(nama_kec, 0))

col_kiri, col_kanan = st.columns([1.5, 1])

with col_kiri:
    st.subheader("🗺️ Peta Sebaran DBD per Kecamatan")
    st.caption("💡 Hover untuk info, klik untuk detail")

    m = folium.Map(
        location=[-6.58, 106.80],
        zoom_start=10,
        tiles="CartoDB positron"
    )

    folium.Choropleth(
        geo_data=geojson_data,
        data=df_year,
        columns=["kecamatan", "jumlah_kasus"],
        key_on="feature.properties.district",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.8,
        line_color="black",
        legend_name=f"Jumlah Kasus DBD {selected_year}",
        nan_fill_color="lightgray",
        highlight=True
    ).add_to(m)

    folium.GeoJson(
        geojson_data,
        style_function=lambda x: {
            "fillOpacity": 0,
            "weight": 1.5,
            "color": "#333333"
        },
        highlight_function=lambda x: {
            "fillOpacity": 0.25,
            "weight": 3,
            "color": "#FF4444"
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["district", "jumlah_kasus"],
            aliases=["Kecamatan:", "Jumlah Kasus:"],
            sticky=True
        ),
        popup=folium.GeoJsonPopup(
            fields=["district", "jumlah_kasus"],
            aliases=["📍 Kecamatan", f"🦟 Kasus DBD {selected_year}"],
            localize=True,
            labels=True,
            style=(
                "background-color: white;"
                "color: #333333;"
                "font-family: Arial;"
                "font-size: 14px;"
                "padding: 10px;"
                "border-radius: 6px;"
                "border: 1px solid #cccccc;"
            )
        )
    ).add_to(m)

    map_data = st_folium(
        m,
        width=900,
        height=550,
        returned_objects=["last_object_clicked_popup"]
    )

with col_kanan:
    st.subheader("📊 Total Kasus per Kecamatan")

    # Panel detail kecamatan diklik
    clicked = map_data.get("last_object_clicked_popup")
    if clicked:
        match = re.search(
            r"📍 Kecamatan.*?<td>(.*?)</td>",
            str(clicked),
            re.DOTALL
        )
        if match:
            nama_klik = match.group(1).strip()
            row = df_year[df_year["kecamatan"] == nama_klik]
            if not row.empty:
                kasus = int(row["jumlah_kasus"].values[0])
                rank = int(
                    df_year["jumlah_kasus"]
                    .rank(ascending=False)
                    .loc[row.index[0]]
                )
                st.info(
                    f"**📍 {nama_klik}**\n\n"
                    f"🦟 Kasus DBD {selected_year}: **{kasus}**\n\n"
                    f"🏅 Peringkat: **{rank} dari {len(df_year)}**"
                )

    df_kecamatan = df_year.sort_values("jumlah_kasus", ascending=True)

    fig = px.bar(
        df_kecamatan,
        x="jumlah_kasus",
        y="kecamatan",
        color="jumlah_kasus",
        color_continuous_scale="YlOrRd",
        text="jumlah_kasus",
        orientation="h"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=850,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Jumlah Kasus",
        yaxis_title="Kecamatan",
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.subheader("🏆 10 Kecamatan dengan Kasus DBD Tertinggi")

top10 = df_year.sort_values("jumlah_kasus", ascending=False).head(10)

fig_top = px.bar(
    top10,
    x="kecamatan",
    y="jumlah_kasus",
    text="jumlah_kasus",
    color="jumlah_kasus",
    color_continuous_scale="Reds"
)
fig_top.update_traces(textposition="outside")
fig_top.update_layout(
    height=500,
    coloraxis_showscale=False,
    xaxis_title="Kecamatan",
    yaxis_title="Jumlah Kasus"
)
st.plotly_chart(fig_top, width="stretch")

st.markdown("---")
st.subheader("📋 Data Kecamatan")

filter_min, filter_max = st.slider(
    "Filter Jumlah Kasus",
    min_value=int(df_year["jumlah_kasus"].min()),
    max_value=int(df_year["jumlah_kasus"].max()),
    value=(
        int(df_year["jumlah_kasus"].min()),
        int(df_year["jumlah_kasus"].max())
    )
)

df_filtered = df_year[
    (df_year["jumlah_kasus"] >= filter_min) &
    (df_year["jumlah_kasus"] <= filter_max)
]

df_show = (
    df_filtered
    .sort_values("jumlah_kasus", ascending=False)
    .reset_index(drop=True)
)
df_show.index += 1
st.dataframe(df_show, width="stretch")

st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; padding:10px; line-height:2;">
        📌 <b>Source Data:</b>
        <a href="https://opendata.bogorkab.go.id/dataset/penderita-penyakit-menular-demam-berdarah-menurut-kecamatan-di-kabupaten-bogor" target="_blank">
            Open Data Kabupaten Bogor
        </a>
        &nbsp;|&nbsp;
        🗺️ <b>GeoJSON Peta:</b>
        <a href="https://github.com/JfrAziz/indonesia-district/blob/master/id32_jawa_barat/id3201_bogor/id3201_bogor.geojson" target="_blank">
            JfrAziz / indonesia-district
        </a>
        <br>
        👨‍💻 <b>Kontributor:</b> Achmad Muhajir
        &nbsp;|&nbsp;
        <a href="https://github.com/Dayyrenn" target="_blank">🔗 My GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
)