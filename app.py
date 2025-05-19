import streamlit as st
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from folium.plugins import MarkerCluster
import time
from loader import show_loader

# Configuration de la page
st.set_page_config(
    page_title="Prédiction du Risque d'Incendie en Californie",
    page_icon="image/fire.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "loader_shown" not in st.session_state:
    show_loader()
    st.session_state["loader_shown"] = True

API_KEY = "3Z6VAUSKV99E8X6SYVGD4VJGL"
API_BASE = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
CALIFORNIA_CENTER = (37.5, -119.5)


# Apply custom CSS for dark theme similar to the image
st.markdown("""
<style>
    .main {
        background-color: #1E1E1E;
        color: white;
    }
    .css-1d391kg {
        background-color: #161616;
    }
    .stApp {
        background-color: #1E1E1E;
    }
    .css-1aumxhk {
        background-color: #1E1E1E;
    }
    .css-18e3th9 {
        padding-top: 0;
    }
    .css-1kyxreq {
        display: flex;
        flex-flow: row wrap;
        row-gap: 1rem;
        justify-content: center;
    }
    .stAlert {
        background-color: rgba(255, 152, 0, 0.2);
        color: white;
    }
    .dashboard-title {
        color: white;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: left;
        padding-left: 10px;
        border-left: 5px solid #d64161;
    }
    .dashboard-subtitle {
        color: rgba(255,255,255,0.6);
        font-size: 16px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #2C2C2C;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-title {
        color: rgba(255,255,255,0.7);
        font-size: 14px;
        margin-bottom: 5px;
    }
    .metric-value {
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    .section-header {
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin: 25px 0 15px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 5px;
    }
    .chart-container {
        background-color: #2C2C2C;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .small-text {
        font-size: 12px;
        color: rgba(255,255,255,0.5);
    }
    .risk-gauge {
        text-align: center;
    }
    /* Custom styling for sidebar */
    .css-16huue1 {
        background-color: #161616 !important;
    }
    div[data-testid="stSidebar"] {
        background-color: #161616;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stSelectbox label, .stSlider label {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    .stDateInput label {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Logo & Header Styling */
    .logo-title-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        padding: 10px;
        background-color: rgba(139, 69, 19, 0.3);
        border-radius: 10px;
    }
    .logo {
        width: 60px;
        height: 60px;
        margin-right: 15px;
    }
    .header-text {
        display: flex;
        flex-direction: column;
    }
</style>
""", unsafe_allow_html=True)

# Fonctions pour le chargement et le traitement des données
@st.cache_data(ttl=3600)
def load_geojson():
    """Charge les données GeoJSON des comtés de Californie"""
    try:
        return gpd.read_file("data/california-counties.geojson")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données géographiques: {e}")
        # Créer un GeoDataFrame simplifié pour la démonstration
        dummy_gdf = gpd.GeoDataFrame({
            'name': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'Fresno'],
            'geometry': None
        })
        return dummy_gdf


@st.cache_data(ttl=3600)
def get_weather_data(location, days=7):
    """Récupère les données météo pour une localisation sur plusieurs jours"""
    url = f"{API_BASE}/{location}?unitGroup=us&key={API_KEY}&contentType=json&include=days"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            # Créer des données météo factices pour la démo
            dummy_data = create_dummy_weather_data(days)
            return dummy_data
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données météo: {e}")
        # Créer des données météo factices pour la démo
        dummy_data = create_dummy_weather_data(days)
        return dummy_data


def create_dummy_weather_data(days=7):
    """Crée des données météo fictives pour la démonstration"""
    today = datetime.now()
    dummy_data = {
        'days': []
    }
    for i in range(days):
        day_data = {
            'datetime': (today + timedelta(days=i)).strftime('%Y-%m-%d'),
            'temp': round(70 + np.random.randint(-10, 10)),
            'humidity': round(50 + np.random.randint(-20, 20)),
            'windspeed': round(5 + np.random.randint(0, 15)),
            'precip': round(np.random.random() * 0.5, 2),
            'conditions': np.random.choice(['Clear', 'Partly Cloudy', 'Cloudy', 'Rain']),
            'icon': np.random.choice(['clear-day', 'partly-cloudy-day', 'cloudy', 'rain'])
        }
        dummy_data['days'].append(day_data)

    return dummy_data


@st.cache_data(ttl=3600)
def get_ndvi_data(county):
    """Simule des données NDVI pour un comté"""
    np.random.seed(hash(county) % 10000)
    base_ndvi = 0.5
    variation = 0.3
    return base_ndvi + (np.random.random() - 0.5) * variation


@st.cache_data(ttl=3600)
def get_elevation_data(county):
    """Simule des données d'élévation pour un comté"""
    np.random.seed(hash(county) % 20000)
    return round(200 + np.random.random() * 500)


def calculate_fire_risk(weather_data, ndvi, elevation):
    """Calcule un score de risque d'incendie basé sur les données météo et environnementales"""
    temp = weather_data.get('temp', 70)
    humidity = weather_data.get('humidity', 50)
    wind = weather_data.get('windspeed', 5)
    precip = weather_data.get('precip', 0)

    # Formule simplifiée pour le risque d'incendie
    base_risk = (temp * 0.3) - (humidity * 0.2) + (wind * 1.5) - (precip * 15) + (ndvi * 10) + (elevation * 0.01)

    # Normaliser entre 0 et 100
    risk = max(0, min(100, base_risk))
    return risk


def get_risk_class(risk_value):
    """Convertit une valeur numérique de risque en classe qualitative"""
    if risk_value < 25:
        return "Faible", "#4CAF50"  # Vert
    elif risk_value < 50:
        return "Modéré", "#FF9800"  # Orange
    elif risk_value < 75:
        return "Élevé", "#F44336"  # Rouge clair
    else:
        return "Extrême", "#B71C1C"  # Rouge foncé


def create_fire_risk_map(counties_data, selected_date):
    """Crée une carte interactive moderne et professionnelle avec les risques d'incendie"""
    m = folium.Map(
        location=CALIFORNIA_CENTER,
        zoom_start=6,
        tiles="CartoDB dark_matter"
    )

    # Overlay titre moderne
    title_html = f'''
    <div style="
        position: fixed;
        top: 30px; left: 50%; transform: translateX(-50%);
        background: linear-gradient(90deg, #232a34 80%, #FF9800 120%);
        padding: 14px 36px 10px 36px;
        border-radius: 18px;
        box-shadow: 0 4px 24px #0008;
        z-index: 9999;
        text-align: center;
        border-left: 10px solid #FF9800;
        font-family: Segoe UI,Roboto,Arial,sans-serif;
    ">
        <span style="font-size:1.7rem;color:#FF9800;font-weight:700;letter-spacing:1px;">🔥 Risque d'Incendie</span>
        <span style="font-size:1.1rem;color:#fff;font-weight:400;"> - {selected_date.strftime('%d/%m/%Y')}</span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Légende stylée et claire
    legend_html = '''
     <div style="
         position: fixed; 
         bottom: 40px; left: 40px; width: 200px; z-index:9999; font-size:15px;
         background:rgba(24,28,36,0.97); color:#fff; border-radius:14px; padding:16px 22px; box-shadow:0 2px 12px #0005;
         font-family: Segoe UI,Roboto,Arial,sans-serif;
     ">
         <b style="font-size:1.15rem;">Légende Risque 🔥</b><br>
         <span style="color:#4CAF50;font-size:1.2em;">●</span> Faible<br>
         <span style="color:#FFEB3B;font-size:1.2em;">●</span> Modéré<br>
         <span style="color:#FF9800;font-size:1.2em;">●</span> Élevé<br>
         <span style="color:#F44336;font-size:1.2em;">●</span> Très élevé<br>
         <span style="color:#B71C1C;font-size:1.2em;">●</span> Extrême
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Palette de couleurs harmonisée
    def folium_color(risk_class):
        if risk_class == "Faible":
            return "#4CAF50"
        elif risk_class == "Modéré":
            return "#FFEB3B"
        elif risk_class == "Élevé":
            return "#FF9800"
        elif risk_class == "Extrême":
            return "#B71C1C"
        else:
            return "#F44336"

    # Marqueurs stylés et cercles avec effet glow
    for idx, row in counties_data.iterrows():
        county_name = row['name']
        risk_value = row['fire_risk']
        risk_class, color = get_risk_class(risk_value)
        coords = CALIFORNIA_COUNTIES.get(county_name, CALIFORNIA_CENTER)

        # Cercle avec effet glow
        folium.Circle(
            location=coords,
            radius=22000,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.22,
            weight=7,
            opacity=0.38
        ).add_to(m)

        # Marqueur avec popup stylé et emoji
        folium.Marker(
            location=coords,
            popup=folium.Popup(f"""
                <div style='min-width:220px; font-family:Segoe UI,Roboto,Arial,sans-serif; background:#232a34; color:#fff; border-radius:14px; padding:16px 18px; border-left:8px solid {color}; box-shadow:0 2px 16px #0008;'>
                    <h4 style='margin-bottom:10px; color:{color}; font-size:1.25rem; letter-spacing:1px;'>{county_name} 🔥</h4>
                    <b>Risque&nbsp;:</b> <span style='color:{color}; font-weight:700;'>{risk_class}</span><br>
                    <b>Score&nbsp;:</b> <span style='font-weight:700; color:{color}; font-size:1.3rem;'>{risk_value:.1f}/100</span>
                </div>
            """, max_width=300),
            icon=folium.Icon(color=None, icon="fire", prefix="fa", icon_color=color),  # Couleur dynamique
            tooltip=f"{county_name}: {risk_class}"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def create_advanced_fire_risk_map(counties_data, selected_date, geojson_path="data/california-counties.geojson"):
    # Charger le GeoJSON des comtés
    gdf = gpd.read_file(geojson_path)
    m = folium.Map(location=CALIFORNIA_CENTER, zoom_start=6, tiles="CartoDB positron")  # Fond clair et moderne

    # Fusionner les risques avec le GeoDataFrame
    merged = gdf.merge(counties_data, left_on="name", right_on="name", how="left")

    # Correction : convertir tous les Timestamp en string (sécurité)
    for col in merged.columns:
        if merged[col].dtype.name.startswith("datetime") or "Timestamp" in str(merged[col].dtype):
            merged[col] = merged[col].astype(str)

    # Palette personnalisée pour un rendu plus pro
    color_scale = ['#4CAF50', '#FFEB3B', '#FF9800', '#F44336', '#B71C1C']

    folium.Choropleth(
        geo_data=merged,
        name="Risque d'incendie",
        data=merged,
        columns=["name", "fire_risk"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",  # Peut être remplacé par 'YlOrBr' ou 'RdYlBu' pour tester
        fill_opacity=0.85,
        line_opacity=0.4,
        line_color="#232a34",
        legend_name="Risque d'incendie",
        nan_fill_color="#bdbdbd"
    ).add_to(m)

    # Popups détaillés avec couleurs dynamiques
    for _, row in merged.iterrows():
        if pd.isna(row['fire_risk']):
            continue
        risk_class, color = get_risk_class(row['fire_risk'])
        popup_html = f"""
        <div style='min-width:200px; font-family:Segoe UI,Roboto,Arial,sans-serif; background:#232a34; color:#fff; border-radius:10px; padding:12px 14px; border-left:6px solid {color};'>
            <h4 style='margin-bottom:6px; color:{color};'>{row['name']} 🔥</h4>
            <b>Risque&nbsp;:</b> <span style='color:{color}; font-weight:700;'>{row['fire_risk']:.1f}/100</span><br>
            <b>Niveau&nbsp;:</b> <span style='color:{color}; font-weight:600;'>{risk_class}</span><br>
            <b>Date&nbsp;:</b> <span style='color:#FFEB3B;'>{selected_date.strftime('%d/%m/%Y')}</span>
        </div>
        """
        folium.Marker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            popup=folium.Popup(popup_html, max_width=260),
            icon=folium.Icon(color="orange", icon="fire", prefix="fa"),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# Coordonnées approximatives des comtés de Californie pour la démonstration
CALIFORNIA_COUNTIES = {
    "Los Angeles": (34.0522, -118.2437),
    "San Diego": (32.7157, -117.1611),
    "San Francisco": (37.7749, -122.4194),
    "Sacramento": (38.5816, -121.4944),
    "Fresno": (36.7378, -119.7871),
    "Alameda": (37.6017, -121.7195),
    "Orange": (33.7175, -117.8311),
    "Santa Clara": (37.3541, -121.9552),
    "Riverside": (33.9533, -117.3962),
    "San Bernardino": (34.1083, -117.2898)
}

# Variables globales pour les paramètres
SHOW_HISTORICAL_FIRES = True


def main():
    # ===== SIDEBAR =====
    st.sidebar.title("Paramètres")
    st.sidebar.subheader("Région")
    counties = ["Tous les comtés", "Los Angeles", "San Diego", "San Francisco", "Sacramento", "Fresno"]
    selected_county = st.sidebar.selectbox("Sélectionner un comté", counties)

    st.sidebar.subheader("Période")
    today = datetime.now().date()
    selected_date = st.sidebar.date_input("Date de prévision", today, min_value=today, max_value=today + timedelta(days=6))

    st.sidebar.subheader("Paramètres avancés")
    global SHOW_HISTORICAL_FIRES
    SHOW_HISTORICAL_FIRES = st.sidebar.checkbox("Afficher les incendies historiques", True)

    st.sidebar.markdown("---")
    st.sidebar.info("""
    **À propos**

    Cette application affiche et prédit le risque d'incendie de forêt en Californie, comté par comté, à partir de données météorologiques et environnementales récentes.
    """)

    page = st.sidebar.radio("Navigation", ("Carte des risques", "Prédiction personnalisée"), index=0)

    if page == "Carte des risques":
        st.markdown("""
        <div style="text-align:center; margin-bottom:1.5rem;">
            <span style="font-size:2.5rem; font-weight:700; color:#FF9800;">🔥 Carte du Risque d'Incendie en Californie</span>
        </div>
        """, unsafe_allow_html=True)

        location = "california" if selected_county == "Tous les comtés" else selected_county.lower().replace(" ", "")
        with st.spinner("Chargement des données météo..."):
            weather_data = get_weather_data(location)

        if not weather_data:
            st.error("Impossible de récupérer les données météorologiques.")
            return

        # Données comtés + calcul du risque
        counties_data = pd.DataFrame({
            'name': list(CALIFORNIA_COUNTIES.keys()) if selected_county == "Tous les comtés" else [selected_county]
        })

        counties_data['fire_risk'] = 0
        day_diff = (selected_date - today).days
        day_data = weather_data['days'][min(day_diff, len(weather_data['days']) - 1)]

        for idx, row in counties_data.iterrows():
            name = row['name']
            ndvi = get_ndvi_data(name)
            elevation = get_elevation_data(name)
            risk = calculate_fire_risk(day_data, ndvi, elevation)
            counties_data.at[idx, 'fire_risk'] = risk

        # === NOUVELLE MISE EN PAGE : Carte à droite, risque à gauche ===
        col_left, col_right = st.columns([1.1, 1.9], gap="large")

        with col_right:
            st.markdown('<h3 style="color:white; text-align:center;">🗺️ Vue Globale du Risque</h3>', unsafe_allow_html=True)
            m = create_fire_risk_map(counties_data, selected_date)
            folium_static(m, width=900, height=600)

        with col_left:
            # Résumé du risque moyen - version stylée et moderne
            avg_risk = counties_data['fire_risk'].mean() if selected_county == "Tous les comtés" else counties_data['fire_risk'].values[0]
            risk_class, risk_color = get_risk_class(avg_risk)
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #232a34 70%, {risk_color} 120%);
                border-radius: 18px;
                box-shadow: 0 6px 24px 0 rgba(0,0,0,0.25);
                padding: 32px 28px 24px 28px;
                margin-bottom: 28px;
                border-left: 10px solid {risk_color};
                display: flex;
                flex-direction: column;
                align-items: center;
                position: relative;
                overflow: hidden;
            ">
                <div style="position:absolute; top:-30px; right:-30px; opacity:0.08; font-size:120px; pointer-events:none;">🔥</div>
                <div style="font-size:2.2rem; font-weight:700; color:{risk_color}; letter-spacing:1px; margin-bottom:10px;">
                    Risque d'Incendie
                </div>
                <div style="font-size:4.2rem; font-weight:900; color:{risk_color}; line-height:1; margin-bottom:8px; text-shadow:0 2px 12px #0008;">
                    {avg_risk:.1f}<span style="font-size:2rem; color:#fff;">/100</span>
                </div>
                <div style="font-size:1.5rem; font-weight:600; color:{risk_color}; margin-bottom:12px; text-transform:uppercase; letter-spacing:2px;">
                    {risk_class}
                </div>
                <div style="font-size:1.1rem; color:#bbb; font-style: italic;">
                    {selected_county if selected_county != "Tous les comtés" else "Californie"} – {selected_date.strftime('%d/%m/%Y')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Indicateurs clés en dessous, avec affichage moderne et alignement
            st.markdown('<div class="section-header">📌 Indicateurs Clés</div>', unsafe_allow_html=True)
            temp_c = round((day_data['temp'] - 32) * 5 / 9, 1)
            humidity = day_data.get('humidity', 'N/A')
            windspeed = day_data.get('windspeed', 'N/A')
            ind1, ind2, ind3 = st.columns(3)
            with ind1:
                st.markdown(f"""
                <div class="metric-card" style="border:2px solid #FF9800; background:linear-gradient(135deg,#2C2C2C 70%,#FF9800 120%);">
                    <div style="font-size:32px; margin-bottom:4px; color:#FF9800;">🌡️</div>
                    <div class="metric-title" style="color:#FF9800;">Température</div>
                    <div class="metric-value" style="color:#FF9800;">{temp_c}°C</div>
                </div>
                """, unsafe_allow_html=True)
            with ind2:
                st.markdown(f"""
                <div class="metric-card" style="border:2px solid #2196F3; background:linear-gradient(135deg,#2C2C2C 70%,#2196F3 120%);">
                    <div style="font-size:32px; margin-bottom:4px; color:#2196F3;">💧</div>
                    <div class="metric-title" style="color:#2196F3;">Humidité</div>
                    <div class="metric-value" style="color:#2196F3;">{humidity}%</div>
                </div>
                """, unsafe_allow_html=True)
            with ind3:
                st.markdown(f"""
                <div class="metric-card" style="border:2px solid #4CAF50; background:linear-gradient(135deg,#2C2C2C 70%,#4CAF50 120%);">
                    <div style="font-size:32px; margin-bottom:4px; color:#4CAF50;">💨</div>
                    <div class="metric-title" style="color:#4CAF50;">Vent</div>
                    <div class="metric-value" style="color:#4CAF50;">{windspeed} mph</div>
                </div>
                """, unsafe_allow_html=True)

        # === Prévisions sur 7 jours ===
        st.markdown('<h2 style="color:#FF9800; margin-top:30px;">📅 Prévisions météo & risque (7 jours)</h2>', unsafe_allow_html=True)
        with st.expander(
            "🔎 Afficher les prévisions détaillées sur 7 jours",
            expanded=True,
        ):
            forecast_days = min(7, len(weather_data['days']))
            cols = st.columns(forecast_days)
            for i in range(forecast_days):
                day = weather_data['days'][i]
                date = datetime.strptime(day['datetime'], '%Y-%m-%d').strftime('%a %d')
                icon = "☀️" if "clear" in day.get('icon', '') else "🌧️" if "rain" in day.get('icon', '') else "⛅"
                temp = round((day['temp'] - 32) * 5 / 9, 1)
                if selected_county == "Tous les comtés":
                    day_risk = np.mean([calculate_fire_risk(day, get_ndvi_data(c), get_elevation_data(c)) for c in CALIFORNIA_COUNTIES])
                else:
                    day_risk = calculate_fire_risk(day, get_ndvi_data(selected_county), get_elevation_data(selected_county))
                risk_class, color = get_risk_class(day_risk)
                bg_gradient = f"linear-gradient(135deg, #232a34 60%, {color} 120%)"
                border = f"3px solid {color}"
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: {bg_gradient};
                        border-radius: 14px;
                        text-align: center;
                        padding: 18px 8px 14px 8px;
                        margin-bottom: 8px;
                        border: {border};
                        box-shadow: 0 2px 12px {color}33;
                        min-width: 120px;
                        ">
                        <div style="font-size:1.2rem; font-weight:700; color:{color}; margin-bottom:2px;">{date}</div>
                        <div style="font-size:2.1rem; margin-bottom:2px;">{icon}</div>
                        <div style="font-size:1.1rem; color:#fff; margin-bottom:2px;">{temp}°C</div>
                        <div style="font-size:1.1rem; font-weight:600; color:{color}; margin-bottom:2px;">{risk_class}</div>
                        <div style="font-size:1.1rem; color:{color};">{int(day_risk)}/100</div>
                    </div>
                    """, unsafe_allow_html=True)

        # === Graphiques ===
        st.markdown('<h2 style="color:#FF9800; margin-top:30px;">📈 Évolution des Indicateurs Météo</h2>', unsafe_allow_html=True)
        with st.expander(
            "📊 Afficher l'évolution météo sur 7 jours",
            expanded=False,
        ):
            dates = [datetime.strptime(d['datetime'], '%Y-%m-%d').strftime('%d/%m') for d in weather_data['days']]
            temp_c = [round((d['temp'] - 32) * 5 / 9, 1) for d in weather_data['days']]
            hum = [d['humidity'] for d in weather_data['days']]
            wind = [d['windspeed'] for d in weather_data['days']]
            fig1 = px.line(x=dates, y=temp_c, title="Température (°C)", labels={"x": "Date", "y": "Temp"})
            fig1.update_layout(plot_bgcolor="#232a34", paper_bgcolor="#232a34", font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
            fig2 = px.line(x=dates, y=hum, title="Humidité (%)", labels={"x": "Date", "y": "Humidité"})
            fig2.update_layout(plot_bgcolor="#232a34", paper_bgcolor="#232a34", font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
            fig3 = px.line(x=dates, y=wind, title="Vent (mph)", labels={"x": "Date", "y": "Vent"})
            fig3.update_layout(plot_bgcolor="#232a34", paper_bgcolor="#232a34", font_color="white")
            st.plotly_chart(fig3, use_container_width=True)

    elif page == "Prédiction personnalisée":
        st.markdown('<h1 class="main-header">Prédiction Personnalisée</h1>', unsafe_allow_html=True)
        with st.expander("Entrer vos propres indicateurs pour une prédiction personnalisée", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                temp_input_c = st.number_input("Température (°C)", -10, 50, 24)
                ndvi_input = st.slider("NDVI", 0.0, 1.0, 0.5)
            with col2:
                humidity_input = st.number_input("Humidité (%)", 0, 100, 50)
                elevation_input = st.number_input("Élévation (m)", 0, 4000, 300)
            with col3:
                wind_input = st.number_input("Vent (mph)", 0, 100, 10)
                precip_input = st.number_input("Précipitations (inches)", 0.0, 5.0, 0.0, step=0.01)

            if st.button("Prédire le risque"):
                temp_f = temp_input_c * 9 / 5 + 32
                data = {
                    'temp': temp_f,
                    'humidity': humidity_input,
                    'windspeed': wind_input,
                    'precip': precip_input
                }
                risk = calculate_fire_risk(data, ndvi_input, elevation_input)
                risk_class, risk_color = get_risk_class(risk)
                st.markdown(f"""
                <div class="card" style="margin-top:10px; border-left:5px solid {risk_color}; background:#232a34;">
                    <h3 style="margin:0; color:{risk_color};">Risque d'Incendie: {risk_class}</h3>
                    <p style="font-size:2rem; font-weight:bold; margin:5px 0; color:{risk_color};">{risk:.1f}/100</p>
                    <p style="margin:0;">Température saisie : {temp_input_c}°C</p>
                </div>
                """, unsafe_allow_html=True)



# Exécuter l'application
if __name__ == "__main__":
    main()