import streamlit as st
import time

def show_loader(duration=6):
    css = """
    <style>
        .fade-out {
            animation: fadeOut 1s ease-in-out forwards;
            animation-delay: 5s;
        }
        @keyframes fadeOut {
            from {opacity: 1;}
            to {opacity: 0;}
        }
    </style>
    """
    
    audio = """
    <audio autoplay>
        <source src="https://www.soundjay.com/nature/sounds/fire-1.mp3" type="audio/mpeg">
        Votre navigateur ne supporte pas l'audio.
    </audio>
    """

    loading_html = f"""
    {css}
    {audio}
    <div id="loader" class="fade-out">
        <div style="text-align: center; padding-top: 100px;">
            <img src="https://plenamata.eco/wp-content/uploads/2021/09/025-incêndio-florestal_v3.gif" alt="loading" width="700"/>
            <h3>Chargement en cours...</h3>
        </div>
    </div>
    """

    loader_placeholder = st.empty()
    loader_placeholder.markdown(loading_html, unsafe_allow_html=True)
    time.sleep(duration)
    loader_placeholder.empty()
