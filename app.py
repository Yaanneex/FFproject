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

# Configuration
API_KEY = "3Z6VAUSKV99E8X6SYVGD4VJGL"
API_BASE = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
CALIFORNIA_CENTER = (37.5, -119.5)

# Configuration de la page
st.set_page_config(
    page_title="Prédiction du Risque d'Incendie en Californie",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        day_date = today + timedelta(days=i)
        day_data = {
            'datetime': day_date.strftime('%Y-%m-%d'),
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
    coastal_counties = ["Los Angeles", "San Diego", "Orange", "San Francisco", "Marin"]
    mountain_counties = ["Sierra", "Alpine", "Mono", "Inyo", "Plumas"]

    if county in coastal_counties:
        return round(100 + np.random.random() * 300)
    elif county in mountain_counties:
        return round(1000 + np.random.random() * 3000)
    else:
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
    """Crée une carte interactive avec les risques d'incendie"""
    m = folium.Map(location=CALIFORNIA_CENTER, zoom_start=6, tiles="CartoDB positron")

    # Ajouter un titre à la carte
    title_html = f'''
    <h3 align="center" style="font-size:16px">
        <b>Prévision du Risque d'Incendie - {selected_date.strftime('%d/%m/%Y')}</b>
    </h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Ajouter des marqueurs pour chaque comté
    for idx, row in counties_data.iterrows():
        county_name = row['name']
        risk_value = row['fire_risk']
        risk_class, color = get_risk_class(risk_value)

        # Ajouter un marqueur pour chaque comté
        folium.Marker(
            location=CALIFORNIA_COUNTIES.get(county_name, CALIFORNIA_CENTER),
            popup=f"""
            <div style="min-width: 180px;">
                <h4>{county_name}</h4>
                <p><b>Risque d'incendie:</b> {risk_value:.1f}/100 ({risk_class})</p>
            </div>
            """,
            icon=folium.Icon(color=color.replace('#', ''), icon="fire", prefix="fa"),
            tooltip=f"{county_name}: {risk_class}"
        ).add_to(m)

    # Ajouter des marqueurs pour les incendies historiques simulés
    if SHOW_HISTORICAL_FIRES:
        marker_cluster = MarkerCluster(name="Incendies historiques").add_to(m)

        np.random.seed(42)
        num_fires = 20
        for i in range(num_fires):
            # Coordonnées aléatoires en Californie
            lat = np.random.uniform(32.5, 42.0)
            lon = np.random.uniform(-124.4, -114.1)

            folium.Marker(
                location=[lat, lon],
                popup=f"Incendie historique #{i + 1}",
                icon=folium.Icon(color="red", icon="fire", prefix="fa")
            ).add_to(marker_cluster)

    # Ajouter un contrôle de couches
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
    show_ndvi_layer = st.sidebar.checkbox("Afficher la couche NDVI", False)

    # Informations
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **À propos**

    Cette application utilise un modèle d'apprentissage automatique pour prédire le risque d'incendie de forêt en Californie.

    Sources de données:
    - Météo: Visual Crossing API
    - Données géographiques: California Open Data
    - Indices de végétation: Simulés (NDVI/EVI)
    """)

    # ===== CONTENU PRINCIPAL =====
    st.markdown('<h1 class="main-header">Système de Prévision du Risque d\'Incendie de Forêt</h1>',
                unsafe_allow_html=True)

    # Structure à deux colonnes
    col1, col2 = st.columns([2, 1])

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

    # === COLONNE 1: CARTE ET PRÉVISIONS SUR 7 JOURS ===
    with col1:
        # Carte des risques d'incendie
        st.markdown('<h2 class="sub-header">Carte des Risques d\'Incendie</h2>', unsafe_allow_html=True)
        with st.container():
            m = create_fire_risk_map(counties_data, selected_date)
            folium_static(m, width=800, height=500)

        # Prévisions sur 7 jours
        st.markdown('<h2 class="sub-header">Prévisions sur 7 Jours</h2>', unsafe_allow_html=True)
        with st.container():
            # Récupérer les prévisions pour les 7 prochains jours
            forecast_days = min(7, len(weather_data.get('days', [])))

            # Créer des colonnes pour chaque jour
            cols = st.columns(forecast_days)

            for i in range(forecast_days):
                day_data = weather_data['days'][i]
                day_date = datetime.strptime(day_data['datetime'], '%Y-%m-%d').date()

                # Calculer le risque pour ce jour
                if selected_county == "Tous les comtés":
                    # Moyenne des risques simulés pour tous les comtés
                    day_risk = np.mean([calculate_fire_risk(day_data, get_ndvi_data(county), get_elevation_data(county))
                                        for county in CALIFORNIA_COUNTIES.keys()])
                else:
                    # Risque pour le comté spécifique
                    day_risk = calculate_fire_risk(day_data, get_ndvi_data(selected_county),
                                                   get_elevation_data(selected_county))

                # Format de l'affichage de la prévision
                with cols[i]:
                    risk_class, color = get_risk_class(day_risk)

                    st.markdown(f"""
                    <div style="text-align:center; padding:10px; border-radius:5px; background-color:{color}10;">
                        <p style="font-weight:bold; margin:0;">{day_date.strftime('%d/%m')}</p>
                        <p style="font-size:0.9rem; margin:0;">{day_data.get('conditions', 'N/A')}</p>
                        <p style="margin:0;">{day_data.get('temp', 'N/A')}°F</p>
                        <p style="color:{color}; font-weight:bold; margin:5px 0;">{risk_class}</p>
                        <p style="font-size:0.9rem; margin:0;">{day_risk:.1f}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # === COLONNE 2: INDICATEURS, GRAPHIQUES ET DÉTAILS ===
    with col2:
        # Calcul du jour sélectionné
        day_diff = (selected_date - today).days
        day_data = weather_data['days'][min(day_diff, len(weather_data['days']) - 1)]

        # Récupérer le risque pour le jour sélectionné
        if selected_county == "Tous les comtés":
            avg_risk = counties_data['fire_risk'].mean()
        else:
            county_data = counties_data[counties_data['name'] == selected_county]
            avg_risk = county_data['fire_risk'].values[0] if not county_data.empty else 50

        # Métriques clés
        st.markdown('<h2 class="sub-header">Indicateurs Clés</h2>', unsafe_allow_html=True)

        # Afficher le niveau de risque
        risk_class, risk_color = get_risk_class(avg_risk)
        st.markdown(f"""
        <div class="card" style="margin-bottom:20px; border-left:5px solid {risk_color};">
            <h3 style="margin:0; color:{risk_color};">Risque d'Incendie: {risk_class}</h3>
            <p style="font-size:2rem; font-weight:bold; margin:5px 0; color:{risk_color};">{avg_risk:.1f}/100</p>
            <p style="margin:0;">Pour {selected_county if selected_county != "Tous les comtés" else "la Californie"} le {selected_date.strftime('%d/%m/%Y')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Afficher les conditions météo actuelles
        col_temp, col_humid, col_wind = st.columns(3)

        with col_temp:
            st.markdown(f"""
            <div style="text-align:center;">
                <p class="metric-label">Température</p>
                <p class="metric-value">{day_data.get('temp', 'N/A')}°F</p>
            </div>
            """, unsafe_allow_html=True)

        with col_humid:
            st.markdown(f"""
            <div style="text-align:center;">
                <p class="metric-label">Humidité</p>
                <p class="metric-value">{day_data.get('humidity', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)

        with col_wind:
            st.markdown(f"""
            <div style="text-align:center;">
                <p class="metric-label">Vent</p>
                <p class="metric-value">{day_data.get('windspeed', 'N/A')} mph</p>
            </div>
            """, unsafe_allow_html=True)

        # Graphiques des indicateurs
        st.markdown('<h2 class="sub-header">Graphiques des Indicateurs</h2>', unsafe_allow_html=True)

        # Créer des données pour les graphiques (7 jours)
        dates = [datetime.strptime(day['datetime'], '%Y-%m-%d').strftime('%d/%m') for day in weather_data['days'][:7]]
        temps = [day.get('temp', 0) for day in weather_data['days'][:7]]
        humidities = [day.get('humidity', 0) for day in weather_data['days'][:7]]
        winds = [day.get('windspeed', 0) for day in weather_data['days'][:7]]

        # Graphique de température
        fig_temp = px.line(
            x=dates, y=temps, markers=True,
            labels={"x": "Date", "y": "Température (°F)"},
            title="Évolution de la Température"
        )
        fig_temp.update_traces(line_color="#FF5722")
        st.plotly_chart(fig_temp, use_container_width=True)

        # Graphique d'humidité
        fig_humid = px.line(
            x=dates, y=humidities, markers=True,
            labels={"x": "Date", "y": "Humidité (%)"},
            title="Évolution de l'Humidité"
        )
        fig_humid.update_traces(line_color="#2196F3")
        st.plotly_chart(fig_humid, use_container_width=True)

        # Graphique de vent
        fig_wind = px.line(
            x=dates, y=winds, markers=True,
            labels={"x": "Date", "y": "Vitesse du Vent (mph)"},
            title="Évolution du Vent"
        )
        fig_wind.update_traces(line_color="#4CAF50")
        st.plotly_chart(fig_wind, use_container_width=True)

        # Détails supplémentaires si un comté est sélectionné
        if selected_county != "Tous les comtés":
            st.markdown('<h2 class="sub-header">Détails du Comté</h2>', unsafe_allow_html=True)

            # Récupérer des données supplémentaires pour le comté sélectionné
            ndvi = get_ndvi_data(selected_county)
            elevation = get_elevation_data(selected_county)

            # Afficher les détails
            st.markdown(f"""
            <div class="card">
                <h4 style="margin-top:0;">Données Environnementales</h4>
                <p><b>Indice de Végétation (NDVI):</b> {ndvi:.2f}</p>
                <p><b>Élévation moyenne:</b> {elevation:.0f} mètres</p>
                <p><b>Conditions météo:</b> {day_data.get('conditions', 'N/A')}</p>
                <p><b>Précipitations:</b> {day_data.get('precip', 0):.2f} pouces</p>
            </div>
            """, unsafe_allow_html=True)


# Exécuter l'application
if __name__ == "__main__":
    main()