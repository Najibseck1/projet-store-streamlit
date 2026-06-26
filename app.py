import streamlit as st
import pandas as pd
import plotly.express as px
from config import DATA_PATH, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER

# --- 1. CONFIGURATION DE LA PAGE (DOIT ÊTRE LA PREMIÈRE INSTRUCTION) ---
st.set_page_config(
    page_title="Dashboard BI - Analyse Clients E-Commerce",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CHARGEMENT DES DONNÉES AVEC MISE EN CACHE ---
@st.cache_data(ttl=3600)
def load_data(path):
    import os
    # Si le fichier local n'existe pas (cas de Streamlit Cloud), on utilise le lien direct Google Drive de l'examen
    if not os.path.exists(path):
        # Lien de téléchargement direct extrait de l'ID du Drive de l'examen
        path = "https://docs.google.com/uc?export=download&id=18RtaRhnXO1ISBq6WU5gfQ8SQ7bQP0AaM"
    
    df = pd.read_csv(path)
    # Conversion des colonnes de dates au format datetime standard
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])
    return df

# --- EXÉCUTION DU CHARGEMENT (LA CORRECTION EST ICI) ---
try:
    df_raw = load_data(DATA_PATH)
except Exception as e:
    st.error(f"Erreur lors du chargement des données. Détails : {e}")
    st.stop()


# --- 3. SIDERBAR & FILTRES (Deux types de filtres différents demandés) ---
with st.sidebar:
    st.header("⚙️ Filtres de Recherche")
    st.markdown("---")
    
    # Filtre 1 : Sélection multiple (Type catégoriel) - Filtre par Segment de clientèle
    all_segments = sorted(df_raw["Segment"].unique())
    selected_segments = st.multiselect(
        "Filtrer par Segment de Clientèle :",
        options=all_segments,
        default=all_segments  # Sélectionne tout par défaut
    )
    
    # Filtre 2 : Sélection de plage de dates (Type temporel) - Filtre par Période de commande
    min_date = df_raw["Order Date"].min().date()
    max_date = df_raw["Order Date"].max().date()
    
    start_date, end_date = st.date_input(
        "Sélectionnez la période d'analyse :",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# --- 4. FILTRAGE DU DATAFRAME ---
filtered_df = df_raw[
    (df_raw["Segment"].isin(selected_segments)) &
    (df_raw["Order Date"].dt.date >= start_date) &
    (df_raw["Order Date"].dt.date <= end_date)
]

# Sécurité si les filtres masquent toutes les lignes
if filtered_df.empty:
    st.warning("⚠️ Aucun résultat ne correspond à vos filtres. Veuillez élargir vos critères de recherche.")
    st.stop()

# --- 5. EN-TÊTE PRINCIPAL ---
st.title("📊 Dashboard Performance & Connaissance Client (USA)")
st.markdown("Ce tableau de bord BI permet d'analyser le comportement d'achat et la profitabilité de vos clients pour optimiser les campagnes marketing.")
st.markdown("---")

# --- 6. INDICATEURS CLÉS (KPIs) ---
total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_customers = filtered_df["Customer ID"].nunique()
profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="💰 Chiffre d'Affaires Global", value=f"${total_sales:,.2f}")
with col2:
    st.metric(label="📈 Bénéfice Net Total", value=f"${total_profit:,.2f}")
with col3:
    st.metric(label="👥 Nombre de Clients Actifs", value=f"{total_customers:,}")
with col4:
    st.metric(label="📊 Marge Bénéficiaire", value=f"{profit_margin:.2f} %")

st.markdown("---")

# --- 7. STRUCTURE EN ONGLETS POUR UNE MEILLEURE CLARTÉ ---
tab1, tab2, tab3 = st.tabs(["👥 Top/Flop Clients", "🌎 Analyse Géographique", "📋 Liste des Données"])

# ==========================================
# ONGLET 1 : ANALYSE DU TOP / FLOP CLIENTS
# ==========================================
with tab1:
    st.header("Analyse de la Valeur et Performance des Clients")
    
    # Agrégation des données par client
    df_client_stats = filtered_df.groupby(["Customer ID", "Customer Name"]).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),
        Nombre_Commandes=("Order ID", "nunique")
    ).reset_index()
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("🏆 Clients qui commandent le plus (CA)")
        top_buyers = df_client_stats.sort_values(by="Total_Sales", ascending=False).head(10)
        
        # Graphique 1 : Diagramme en barres horizontales (Volume de ventes)
        fig_sales = px.bar(
            top_buyers, x="Total_Sales", y="Customer Name", orientation='h',
            title="Top 10 des clients par volume d'achat cumulé (en $)",
            labels={"Total_Sales": "Chiffre d'Affaires ($)", "Customer Name": "Nom du Client"},
            color_discrete_sequence=[COLOR_PRIMARY]
        )
        fig_sales.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sales, use_container_width=True)
        
    with col_c2:
        st.subheader("💸 Clients les plus rentables (Profit)")
        top_profitable = df_client_stats.sort_values(by="Total_Profit", ascending=False).head(10)
        
        # Graphique 2 : Diagramme en barres horizontales (Bénéfices générés)
        fig_profit = px.bar(
            top_profitable, x="Total_Profit", y="Customer Name", orientation='h',
            title="Top 10 des clients générant le plus de bénéfice net (en $)",
            labels={"Total_Profit": "Bénéfice Réalisé ($)", "Customer Name": "Nom du Client"},
            color_discrete_sequence=[COLOR_SUCCESS]
        )
        fig_profit.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_profit, use_container_width=True)

    st.markdown("---")
    st.subheader("⚠️ Focus Attention : Les clients les moins profitables (Pertes)")
    
    # Extraction des clients déficitaires
    flops_profitable = df_client_stats.sort_values(by="Total_Profit", ascending=True).head(5)
    
    # Graphique 3 : Diagramme en barres pour mettre en avant les pertes
    fig_flop = px.bar(
        flops_profitable, x="Total_Profit", y="Customer Name", orientation='h',
        title="Flop 5 des clients enregistrant le plus de pertes financières (en $)",
        labels={"Total_Profit": "Pertes / Profit net ($)", "Customer Name": "Nom du Client"},
        color_discrete_sequence=[COLOR_DANGER]
    )
    fig_flop.update_layout(yaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_flop, use_container_width=True)

# ==========================================
# ONGLET 2 : ANALYSE GÉOGRAPHIQUE
# ==========================================
with tab2:
    st.header("Analyse de la Rentabilité par Zone Géographique")
    
    # Agrégation des données par État américain
    df_geo_stats = filtered_df.groupby("State").agg(
        CA_Etat=("Sales", "sum"),
        Profit_Etat=("Profit", "sum")
    ).reset_index()
    
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        # Graphique 4 : Carte choroplèthe interactive des États-Unis (Deuxième type de graphique requis)
        fig_map = px.choropleth(
            df_geo_stats,
            locations="State",
            locationmode="USA-states",
            color="Profit_Etat",
            scope="usa",
            title="Répartition géographique des bénéfices par État aux USA",
            labels={"Profit_Etat": "Bénéfice ($)", "State": "État"},
            color_continuous_scale="RdYlGn" # Vert = Rentable, Rouge = Pertes
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
    with col_g2:
        st.subheader("🏢 Top Régions")
        df_region = filtered_df.groupby("Region")["Profit"].sum().reset_index()
        
        # Graphique 5 : Diagramme circulaire (Part de la profitabilité par grande région américaine)
        fig_pie = px.pie(
            df_region, values="Profit", names="Region",
            title="Part des bénéfices par grande Région",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# ONGLET 3 : LISTE DES DONNÉES FILTRÉES
# ==========================================
with tab3:
    st.header("Exploration brute des transactions filtrées")
    st.write("Ce tableau contient l'ensemble des données correspondant aux filtres choisis dans la barre latérale.")
    st.dataframe(
        filtered_df[["Order ID", "Order Date", "Customer Name", "Segment", "State", "Region", "Sales", "Profit"]],
        use_container_width=True,
        height=400
    )