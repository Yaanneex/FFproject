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


# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF5722;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #FF9800;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .risk-high {
        color: #D32F2F;
        font-weight: bold;
    }
    .risk-medium {
        color: #FF9800;
        font-weight: bold;
    }
    .risk-low {
        color: #4CAF50;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #616161;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(135deg, #181c24 0%, #232a34 100%) !important;
    color: #fff !important;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
}
.sidebar .sidebar-content {
    background: #20232a !important;
}
@media (max-width: 768px) {
    .main-header { font-size: 1.5rem !important; }
    .sub-header { font-size: 1.1rem !important; }
    .card { padding: 10px !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Responsive card and header tweaks */
@media (max-width: 900px) {
    .main-header { font-size: 1.3rem !important; }
    .sub-header { font-size: 1rem !important; }
    .card { padding: 8px !important; }
}
.stApp {
    background: linear-gradient(135deg, #181c24 0%, #232a34 100%) !important;
}
.card, .stPlotlyChart {
    background: #232a34 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 12px #0003 !important;
    margin-bottom: 1.2rem !important;
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
    """Crée une carte interactive moderne avec les risques d'incendie"""
    m = folium.Map(location=CALIFORNIA_CENTER, zoom_start=6, tiles="CartoDB dark_matter")

    # Titre moderne
    title_html = f'''
    <div style="background:rgba(24,28,36,0.95);padding:8px 0 4px 0;border-radius:10px;margin:10px auto;width:340px;text-align:center;">
        <span style="font-size:1.2rem;color:#FF9800;font-weight:700;">🔥 Prévision du Risque d'Incendie</span>
        <span style="font-size:1rem;color:#fff;font-weight:400;"> - {selected_date.strftime('%d/%m/%Y')}</span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Palette de couleurs pour les risques
    def folium_color(risk_class):
        if risk_class == "Faible":
            return "green"
        elif risk_class == "Modéré":
            return "orange"
        elif risk_class == "Élevé":
            return "red"
        else:
            return "darkred"

    # Ajout d'une légende personnalisée
    legend_html = '''
     <div style="
         position: fixed; 
         bottom: 40px; left: 40px; width: 180px; z-index:9999; font-size:14px;
         background:rgba(24,28,36,0.95); color:#fff; border-radius:10px; padding:10px 16px; box-shadow:0 2px 8px #0003;">
         <b>Légende Risque 🔥</b><br>
         <span style="color:#4CAF50;">●</span> Faible<br>
         <span style="color:#FF9800;">●</span> Modéré<br>
         <span style="color:#F44336;">●</span> Élevé<br>
         <span style="color:#B71C1C;">●</span> Extrême
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Ajouter des marqueurs pour chaque comté
    for idx, row in counties_data.iterrows():
        county_name = row['name']
        risk_value = row['fire_risk']
        risk_class, color = get_risk_class(risk_value)
        folium_col = folium_color(risk_class)
        coords = CALIFORNIA_COUNTIES.get(county_name, CALIFORNIA_CENTER)

        # Cercle coloré pour visualiser le niveau de risque
        folium.Circle(
            location=coords,
            radius=20000,
            color=folium_col,
            fill=True,
            fill_color=folium_col,
            fill_opacity=0.28,
            weight=2
        ).add_to(m)

        # Marqueur avec popup stylé et emoji
        folium.Marker(
            location=coords,
            popup=folium.Popup(f"""
                <div style='min-width:200px; font-family:Segoe UI,Roboto,Arial,sans-serif; background:#232a34; color:#fff; border-radius:8px; padding:10px 12px;'>
                    <h4 style='margin-bottom:6px; color:#FF9800;'>{county_name} 🔥</h4>
                    <b>Risque&nbsp;:</b> <span style='color:{color}; font-weight:700;'>{risk_class}</span><br>
                    <b>Score&nbsp;:</b> <span style='font-weight:600;'>{risk_value:.1f}/100</span>
                </div>
            """, max_width=260),
            icon=folium.Icon(color=folium_col, icon="fire", prefix="fa"),
            tooltip=f"{county_name}: {risk_class}"
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


# Fonction principale de l'application
def main():
    # ===== SIDEBAR =====
    st.sidebar.title("Paramètres")
    # Sélection de la région
    st.sidebar.subheader("Région")
    counties = ["Tous les comtés", "Los Angeles", "San Diego", "San Francisco", "Sacramento", "Fresno"]
    selected_county = st.sidebar.selectbox("Sélectionner un comté", counties)

    # Sélection de la date
    st.sidebar.subheader("Période")
    today = datetime.now().date()
    selected_date = st.sidebar.date_input("Date de prévision", today, min_value=today,
                                          max_value=today + timedelta(days=6))

    # Paramètres avancés
    st.sidebar.subheader("Paramètres avancés")
    global SHOW_HISTORICAL_FIRES
    SHOW_HISTORICAL_FIRES = st.sidebar.checkbox("Afficher les incendies historiques", True)

    # Informations
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **À propos**

    Cette application affiche et prédit le risque d'incendie de forêt en Californie, comté par comté, à partir de données météorologiques et environnementales récentes.
    """)

    # Choix de la page (doit être AVANT tout if page == ...)
    page = st.sidebar.radio(
        "Navigation",
        ("Prédiction régionale", "Prédiction personnalisée"),
        index=0
    )

    if page == "Prédiction régionale":
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <span style="font-size:2.5rem; font-weight:700; color:#FF9800;">🔥</span>
            <span style="font-size:2.2rem; font-weight:700; color:#fff;">Prévision Risque Incendie Californie</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<h1 class="main-header">Système de Prévision du Risque d\'Incendie de Forêt</h1>', unsafe_allow_html=True)

        # Récupérer les données météo
        location = "california" if selected_county == "Tous les comtés" else selected_county.lower().replace(" ", "")
        with st.spinner("Récupération des données météorologiques..."):
            weather_data = get_weather_data(location)

        if not weather_data:
            st.error("Impossible de récupérer les données météorologiques. Veuillez réessayer plus tard.")
            return

        # Préparer les données pour les comtés
        counties_data = pd.DataFrame({
            'name': list(CALIFORNIA_COUNTIES.keys()) if selected_county == "Tous les comtés" else [selected_county]
        })

        # Calculer le risque d'incendie pour chaque comté
        counties_data['fire_risk'] = 0
        day_diff = (selected_date - today).days
        day_data = weather_data['days'][min(day_diff, len(weather_data['days']) - 1)]

        for idx, row in counties_data.iterrows():
            county_name = row['name']
            ndvi = get_ndvi_data(county_name)
            elevation = get_elevation_data(county_name)
            risk = calculate_fire_risk(day_data, ndvi, elevation)
            counties_data.at[idx, 'fire_risk'] = risk

        # === 1. INDICATEURS CLÉS ===
        st.markdown('<h2 class="sub-header">🌡️ Indicateurs Clés</h2>', unsafe_allow_html=True)
        col_temp, col_humid, col_wind = st.columns(3)
        temp_c = round((day_data['temp'] - 32) * 5 / 9, 1) if day_data.get('temp') not in [None, 'N/A'] else 'N/A'
        with col_temp:
            st.markdown(f"""
            <div style="background:#232a34; border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:1.2rem; color:#FF9800;">🌡️ Température</div>
                <div style="font-size:2rem; font-weight:bold;">{temp_c}°C</div>
            </div>
            """, unsafe_allow_html=True)
        with col_humid:
            st.markdown(f"""
            <div style="background:#232a34; border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:1.2rem; color:#2196F3;">💧 Humidité</div>
                <div style="font-size:2rem; font-weight:bold;">{day_data.get('humidity', 'N/A')}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col_wind:
            st.markdown(f"""
            <div style="background:#232a34; border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:1.2rem; color:#4CAF50;">💨 Vent</div>
                <div style="font-size:2rem; font-weight:bold;">{day_data.get('windspeed', 'N/A')} mph</div>
            </div>
            """, unsafe_allow_html=True)

        # === 2. PRÉDICTION SUR 7 JOURS ===
        st.markdown('<h2 class="sub-header">📅 Prévisions sur 7 Jours</h2>', unsafe_allow_html=True)
        forecast_days = min(7, len(weather_data.get('days', [])))
        cols = st.columns(forecast_days)
        for i in range(forecast_days):
            day_data = weather_data['days'][i]
            day_date = datetime.strptime(day_data['datetime'], '%Y-%m-%d').date()
            temp_c = round((day_data['temp'] - 32) * 5 / 9, 1) if day_data.get('temp') not in [None, 'N/A'] else 'N/A'
            icon = "☀️" if "clear" in day_data.get('icon', '').lower() else "🌧️" if "rain" in day_data.get('icon', '').lower() else "⛅"
            if selected_county == "Tous les comtés":
                day_risk = np.mean([calculate_fire_risk(day_data, get_ndvi_data(county), get_elevation_data(county))
                                    for county in CALIFORNIA_COUNTIES.keys()])
            else:
                day_risk = calculate_fire_risk(day_data, get_ndvi_data(selected_county), get_elevation_data(selected_county))
            risk_class, color = get_risk_class(day_risk)
            with cols[i]:
                st.markdown(f"""
                <div style="
                    background: #232a34;
                    border-radius: 18px;
                    padding: 18px 8px 14px 8px;
                    margin-bottom: 8px;
                    box-shadow: 0 2px 8px #0002;
                    text-align: center;
                    color: #fff;
                ">
                    <div style="font-size:1.1rem; font-weight:600; margin-bottom:2px;">{day_date.strftime('%a %d %b')}</div>
                    <div style="font-size:2.2rem; font-weight:bold; margin-bottom:0;">{temp_c}°C</div>
                    <div style="font-size:2.5rem; margin-bottom:0;">{icon}</div>
                    <div style="font-size:1rem; color:#bbb; margin-bottom:4px;">{day_data.get('conditions', 'N/A')}</div>
                    <div style="font-size:0.95rem; margin-bottom:2px;">
                        <span style="color:{color}; font-weight:600;">{risk_class}</span>
                        <span style="color:{color}; font-weight:600;">({day_risk:.0f}/100)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # === 3. RISQUE INCENDIE ===
        st.markdown('<h2 class="sub-header">🔥 Risque d\'Incendie</h2>', unsafe_allow_html=True)
        if selected_county == "Tous les comtés":
            avg_risk = counties_data['fire_risk'].mean()
        else:
            county_data = counties_data[counties_data['name'] == selected_county]
            avg_risk = county_data['fire_risk'].values[0] if not county_data.empty else 50
        risk_class, risk_color = get_risk_class(avg_risk)
        st.markdown(f"""
        <div class="card" style="margin-top:18px; border-left:5px solid {risk_color}; background:#232a34;">
            <h3 style="margin:0; color:{risk_color};">Risque d'Incendie: {risk_class}</h3>
            <p style="font-size:2rem; font-weight:bold; margin:5px 0; color:{risk_color};">{avg_risk:.1f}/100</p>
            <p style="margin:0;">Pour {selected_county if selected_county != "Tous les comtés" else "la Californie"} le {selected_date.strftime('%d/%m/%Y')}</p>
        </div>
        """, unsafe_allow_html=True)

        # === 4. CARTE DES RISQUES EN BAS ===
        st.markdown('<h2 class="sub-header">🗺️ Carte des Risques</h2>', unsafe_allow_html=True)
        m = create_fire_risk_map(counties_data, selected_date)
        folium_static(m, width=800, height=500)



        # === 5. GRAPHIQUES DES INDICATEURS ===
        st.markdown('<h2 class="sub-header">📈 Graphiques des Indicateurs (7 jours)</h2>', unsafe_allow_html=True)
        # Préparer les données pour les graphiques
        dates = [datetime.strptime(day['datetime'], '%Y-%m-%d').strftime('%d/%m') for day in weather_data['days'][:7]]
        temps = [day.get('temp', 0) for day in weather_data['days'][:7]]
        humidities = [day.get('humidity', 0) for day in weather_data['days'][:7]]
        winds = [day.get('windspeed', 0) for day in weather_data['days'][:7]]

        # Conversion des températures en Celsius pour le graphique
        temps_c = [round((t - 32) * 5 / 9, 1) for t in temps]

        # Graphique de température en °C
        fig_temp = px.line(
            x=dates, y=temps_c, markers=True,
            labels={"x": "Date", "y": "Température (°C)"},
            title="Évolution de la Température"
        )
        fig_temp.update_traces(line_color="#FF5722")
        st.plotly_chart(fig_temp, use_container_width=True)

        # Graphique d'humidité
        fig_hum = px.line(
            x=dates, y=humidities, markers=True,
            labels={"x": "Date", "y": "Humidité (%)"},
            title="Évolution de l'Humidité"
        )
        fig_hum.update_traces(line_color="#2196F3")
        st.plotly_chart(fig_hum, use_container_width=True)

        # Graphique de vent
        fig_wind = px.line(
            x=dates, y=winds, markers=True,
            labels={"x": "Date", "y": "Vent (mph)"},
            title="Évolution du Vent"
        )
        fig_wind.update_traces(line_color="#4CAF50")
        st.plotly_chart(fig_wind, use_container_width=True)


    elif page == "Prédiction personnalisée":
        st.markdown('<h1 class="main-header">Prédiction Personnalisée</h1>', unsafe_allow_html=True)
        with st.expander("Entrer vos propres indicateurs pour une prédiction personnalisée", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                temp_input_c = st.number_input("Température (°C)", min_value=-10, max_value=50, value=24, key="custom_temp_c")
                ndvi_input = st.slider("NDVI (Indice de Végétation)", min_value=0.0, max_value=1.0, value=0.5, key="custom_ndvi")
            with col2:
                humidity_input = st.number_input("Humidité (%)", min_value=0, max_value=100, value=50, key="custom_humidity")
                elevation_input = st.number_input("Élévation (m)", min_value=0, max_value=4000, value=300, key="custom_elevation")
            with col3:
                wind_input = st.number_input("Vent (mph)", min_value=0, max_value=100, value=10, key="custom_wind")
                precip_input = st.number_input("Précipitations (inches)", min_value=0.0, max_value=5.0, value=0.0, step=0.01, key="custom_precip")

            if st.button("Prédire le risque d'incendie", key="predict_custom"):
                st.session_state['show_custom_prediction'] = True

            if st.session_state.get('show_custom_prediction', False):
                # Conversion °C -> °F pour la formule
                temp_input = temp_input_c * 9 / 5 + 32
                custom_weather = {
                    'temp': temp_input,
                    'humidity': humidity_input,
                    'windspeed': wind_input,
                    'precip': precip_input
                }
                custom_risk = calculate_fire_risk(custom_weather, ndvi_input, elevation_input)
                risk_class, risk_color = get_risk_class(custom_risk)
                st.markdown(f"""
                <div class="card" style="margin-top:10px; border-left:5px solid {risk_color}; background:#232a34;">
                    <h3 style="margin:0; color:{risk_color};">Risque d'Incendie: {risk_class}</h3>
                    <p style="font-size:2rem; font-weight:bold; margin:5px 0; color:{risk_color};">{custom_risk:.1f}/100</p>
                    <p style="margin:0;">Température saisie : {temp_input_c}°C</p>
                    <p style="margin:0;">Basé sur vos indicateurs personnalisés</p>
                </div>
                """, unsafe_allow_html=True)


# Exécuter l'application
if __name__ == "__main__":
    main()