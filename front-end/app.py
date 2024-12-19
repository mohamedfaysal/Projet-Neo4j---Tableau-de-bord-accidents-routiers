import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.express as px
import pandas as pd
from neo4j import GraphDatabase
import folium
from folium.plugins import MarkerCluster

# Connexion à la base de données Neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "password"
#password ="12345678"

# Connexion à Neo4j
def get_neo4j_session():
    driver = GraphDatabase.driver(uri, auth=(username, password))
    session = driver.session()
    return session


def get_accidents_localises(session):
    query = """
    MATCH (a:Accident)-[:SE_DEROULE_A]->(l:Lieu)
    RETURN l.latitude AS latitude, l.longitude AS longitude, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    LIMIT 200
    """
    result = session.run(query)
    return pd.DataFrame([dict(record) for record in result])

def analyse_localisation():
    session = get_neo4j_session()
    df = get_accidents_localises(session)
    
  
    map_accidents = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
    
    marker_cluster = MarkerCluster().add_to(map_accidents)

    for index, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Accidents: {row['nb_accidents']} incidents",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(marker_cluster)

    st.write("###### **Carte des lieux les plus accidentogènes**")
    st.components.v1.html(map_accidents._repr_html_(), height=500)


def get_accidents_par_heure(session):
    query = """
    MATCH (a:Accident)
    WHERE a.heure IS NOT NULL
    RETURN a.heure AS heure, COUNT(a) AS nb_accidents
    ORDER BY heure
    """
    result = session.run(query)
    return pd.DataFrame([dict(record) for record in result])

def analyse_heure():
    session = get_neo4j_session()
    df = get_accidents_par_heure(session)
    
    fig = px.histogram(df, x="heure", y="nb_accidents", title="Accidents par Heure")
    st.plotly_chart(fig)

climats_dict = {
    -1: "Non enregistré",
    1: "Normale",
    2: "Pluie légère",
    3: "Pluie forte",
    4: "Neige - grêle",
    5: "Brouillard - fumée",
    6: "Vent fort - tempête",
    7: "Temps éblouissant",
    8: "Temps couvert",
    9: "Autre"
}

def get_accidents_par_climat(session):
    query = """
    MATCH (a:Accident)-[r:SE_DEROULE_A]->(l:Lieu)
    WHERE r.climat IS NOT NULL
    RETURN r.climat AS climat, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    
    for record in data:
        record['climat'] = climats_dict.get(record['climat'], 'Inconnu')
    
    return pd.DataFrame(data)

def analyse_climat():
    session = get_neo4j_session()
    df = get_accidents_par_climat(session)
    
    fig = px.bar(df, x='climat', y='nb_accidents',
                 title='Répartition des Accidents par Conditions Climatiques',
                 labels={'climat': 'Conditions Climatiques', 'nb_accidents': 'Nombre d\'Accidents'},
                 color='climat', 
                 color_discrete_map=climats_dict)

    fig.update_layout(
        annotations=[dict(
            x=0.5, y=-0.2,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=12),
            align="center"
        )],
        margin={"t": 20, "b": 60},
        height=500
    )

    st.plotly_chart(fig)


collision_dict = {
    -1: "Non renseigné",
    1: "Deux véhicules - frontale",
    2: "Deux véhicules – par l’arrière",
    3: "Deux véhicules – par le coté",
    4: "Trois véhicules et plus – en chaîne",
    5: "Trois véhicules et plus - collisions multiples",
    6: "Autre collision",
    7: "Sans collision"
}

def get_accidents_par_type_collision(session):
    query = """
    MATCH (a:Accident)
    WHERE a.type_collision IS NOT NULL
    RETURN a.type_collision AS type_collision, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    
    for record in data:
        record['type_collision'] = collision_dict.get(record['type_collision'], 'Inconnu')
    
    return pd.DataFrame(data)


def analyse_collision():
    session = get_neo4j_session()
    df = get_accidents_par_type_collision(session)
    
    fig = px.bar(df, x='type_collision', y='nb_accidents',
                 title='Répartition des Accidents par Type de Collision',
                 labels={'type_collision': 'Type de Collision', 'nb_accidents': 'Nombre d\'Accidents'},
                 color='type_collision', 
                 color_discrete_map=collision_dict)

   
    st.plotly_chart(fig)


def get_accidents_par_mois(session):
    query = """
    MATCH (a:Accident)
    WHERE a.mois IS NOT NULL
    RETURN toInteger(a.mois) AS mois, COUNT(a) AS nb_accidents
    ORDER BY mois
    """
    result = session.run(query)
    return pd.DataFrame([dict(record) for record in result])


def accidents_par_mois():
    session = get_neo4j_session()
    df = get_accidents_par_mois(session)

    mois_noms = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
        7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }
    df["mois_nom"] = df["mois"].map(mois_noms)

    fig = px.bar(
        df, 
        x="mois_nom", 
        y="nb_accidents", 
        title="Accidents par Mois en 2023", 
        labels={"mois_nom": "Mois", "nb_accidents": "Nombre d'Accidents"},
        text="nb_accidents"
    )
    fig.update_traces(texttemplate='%{text}', textposition='inside')

    st.plotly_chart(fig)


VEHICLE_LEGEND = {
    0: "Indéterminable",
    1: "Bicyclette",
    2: "Cyclomoteur <50cm3",
    3: "Voiturette (Quadricycle à moteur carrossé)",
    4: "Référence inutilisée depuis 2006 (scooter immatriculé)",
    5: "Référence inutilisée depuis 2006 (motocyclette)",
    6: "Référence inutilisée depuis 2006 (side-car)",
    7: "VL seul",
    8: "Référence inutilisée depuis 2006 (VL + caravane)",
    9: "Référence inutilisée depuis 2006 (VL + remorque)",
    10: "VU seul 1,5T <= PTAC <= 3,5T avec ou sans remorque",
    11: "Référence inutilisée depuis 2006 (VU (10) + caravane)",
    12: "Référence inutilisée depuis 2006 (VU (10) + remorque)",
    13: "PL seul 3,5T <PTCA <= 7,5T",
    14: "PL seul > 7,5T",
    15: "PL > 3,5T + remorque",
    16: "Tracteur routier seul",
    17: "Tracteur routier + semi-remorque",
    18: "Référence inutilisée depuis 2006 (transport en commun)",
    19: "Référence inutilisée depuis 2006 (tramway)",
    20: "Engin spécial",
    21: "Tracteur agricole",
    30: "Scooter < 50 cm3",
    31: "Motocyclette > 50 cm3 et <= 125 cm3",
    32: "Scooter > 50 cm3 et <= 125 cm3",
    33: "Motocyclette > 125 cm3",
    34: "Scooter > 125 cm3",
    35: "Quad léger <= 50 cm3",
    36: "Quad lourd > 50 cm3",
    37: "Autobus",
    38: "Autocar",
    39: "Train",
    40: "Tramway",
    41: "3RM <= 50 cm3",
    42: "3RM > 50 cm3 <= 125 cm3",
    43: "3RM > 125 cm3",
    50: "EDP à moteur",
    60: "EDP sans moteur",
    80: "VAE",
    99: "Autre véhicule"
}

def get_categories_vehicules(session):
    query = """
    MATCH (v:Vehicule)-[:EST_IMPLIQUE_DANS]->(a:Accident)
    WHERE v.categorie_vehicule IS NOT NULL
    RETURN v.categorie_vehicule AS categorie_vehicule, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    LIMIT 10
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    return pd.DataFrame(data)


def analyse_categories_vehicules():
    session = get_neo4j_session()
    df = get_categories_vehicules(session)

    df["categorie_vehicule_nom"] = df["categorie_vehicule"].map(VEHICLE_LEGEND)

    fig = px.scatter(
        df,
        x="categorie_vehicule_nom", 
        y="nb_accidents",
        size="nb_accidents",
        color="categorie_vehicule_nom",
        title="Catégories de Véhicules Impliquées dans des Accidents",
        labels={"categorie_vehicule_nom": "Catégorie de Véhicule", "nb_accidents": "Nombre d'Accidents"},
        size_max=60,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        xaxis_title="Catégorie de Véhicule",
        yaxis_title="Nombre d'Accidents",
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig)

OBSM_LEGEND = {
    -1: "Non renseigné",
    0: "Aucun",
    1: "Piéton",
    2: "Véhicule",
    4: "Véhicule sur rail",
    5: "Animal domestique",
    6: "Animal sauvage",
    9: "Autre"
}

def get_obstacles(session):
    query = """
    MATCH (v:Vehicule)-[:EST_IMPLIQUE_DANS]->(a:Accident)
    WHERE v.obstacle_mobile_heurt IS NOT NULL
    RETURN v.obstacle_mobile_heurt AS obstacle_mobile, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    return pd.DataFrame(data)


def analyse_obstacles():
    session = get_neo4j_session()
    df = get_obstacles(session)

    df["obstacle_nom"] = df["obstacle_mobile"].map(OBSM_LEGEND)

    fig = px.bar(
    df,
    x="obstacle_nom",
    y="nb_accidents",
    title="Nombre d'Accidents par Type d'Obstacle Mobile",
    labels={"obstacle_nom": "Type d'Obstacle", "nb_accidents": "Nombre d'Accidents"},
    color="obstacle_nom",
    color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(xaxis_title="Type d'Obstacle", yaxis_title="Nombre d'Accidents", height=500)
    st.plotly_chart(fig)


def get_repartition_sexe(session):
    query = """
    MATCH (u:Usager)-[:A_FAIT_UN]->(a:Accident)
    RETURN u.sexe AS sexe, COUNT(a) AS nb_accidents
    """
    result = session.run(query)
    return pd.DataFrame([dict(record) for record in result])

def usagers_sexe():
    session = get_neo4j_session()
    df = get_repartition_sexe(session)
    
    sexe_legend = {
        1: "Homme",
        2: "Femme",
        -1: "Non renseigné"
    }
    df["sexe_label"] = df["sexe"].map(sexe_legend)

    fig = px.pie(
        df, 
        values="nb_accidents", 
        names="sexe_label",
        title="Répartition des Accidents par sexe des Usagers",
        color="sexe_label",
        color_discrete_map={"Homme": "blue", "Femme": "pink", "Non renseigné": "red"}
    )

    st.plotly_chart(fig)


def get_gravite_par_type_usager(session):
    query = """
    MATCH (u:Usager)-[:A_FAIT_UN]->(a:Accident)
    RETURN u.gravite AS gravite, COUNT(u) AS nb_usagers
    """
    result = session.run(query)
    return pd.DataFrame([dict(record) for record in result])


def usagers_gravite():
    session = get_neo4j_session()
    df = get_gravite_par_type_usager(session)
    
    gravite_legend = {
        1: "Indemne",
        2: "Tué",
        3: "Blessé hospitalisé",
        4: "Blessé léger"
    }
    df["gravite_label"] = df["gravite"].map(gravite_legend)

    fig = px.bar(
        df, 
        x="gravite_label", 
        y="nb_usagers", 
        title="Nombre d'usagers par type de gravité",
        labels={"gravite_label": "Gravité", "nb_usagers": "Nombre d'Usagers"},
        text= "nb_usagers",
        color="gravite_label"
    )

    fig.update_traces(texttemplate='%{text}', textposition='outside')

    st.plotly_chart(fig)


def get_ages_usagers(session):
    query = """
    MATCH (u:Usager)-[:A_FAIT_UN]->(a:Accident)
    WHERE u.age IS NOT NULL
    RETURN 2023 - toInteger(u.age) AS age, COUNT(a) AS nb_accidents
    ORDER BY age
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    return pd.DataFrame(data)

def analyse_ages_usagers():
    session = get_neo4j_session()
    df = get_ages_usagers(session)
    
    df = df[(df["age"] > 0) & (df["age"] <= 100)]
    
    fig = px.histogram(
        df,
        x="age",
        y="nb_accidents",
        nbins=20,
        title="Répartition des Âges des Usagers Impliqués dans les Accidents",
        labels={"age": "Âge des Usagers", "nb_accidents": "Nombre d'Accidents"},
        color_discrete_sequence=["#636EFA"]
    )
    
    fig.update_layout(
        xaxis_title="Âge des Usagers",
        yaxis_title="Nombre d'Accidents",
        height=500
    )
    
    st.plotly_chart(fig)


TRIP_LEGEND = {
    -1: "Non renseigné",
    0: "Non renseigné",
    1: "Domicile – travail",
    2: "Domicile – école",
    3: "Courses – achats",
    4: "Utilisation professionnelle",
    5: "Promenade – loisirs",
    9: "Autre"
}

def get_trajets_usagers(session):
    query = """
    MATCH (u:Usager)-[:A_FAIT_UN]->(a:Accident)
    WHERE u.trajet IS NOT NULL
    RETURN u.trajet AS trajet, COUNT(a) AS nb_accidents
    ORDER BY nb_accidents DESC
    """
    result = session.run(query)
    data = [dict(record) for record in result]
    return pd.DataFrame(data)


def analyse_trajets_usagers():
    session = get_neo4j_session()
    df = get_trajets_usagers(session)
    
    df['trajet_libelle'] = df['trajet'].map(TRIP_LEGEND)

    fig = px.bar(
        df,
        x='trajet_libelle',
        y='nb_accidents',
        title="Répartition des Accidents par Type de Trajet des Usagers",
        labels={'trajet_libelle': 'Type de Trajet', 'nb_accidents': 'Nombre d\'Accidents'},
        color='trajet_libelle',
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_layout(
        xaxis_title="Type de Trajet",
        yaxis_title="Nombre d'Accidents",
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig)




def get_accidents_mortels(session):
    query = """
    MATCH (u:Usager)-[:A_FAIT_UN]->(a:Accident)
    WHERE u.gravite = 2
    RETURN COUNT(DISTINCT a) AS accidents_mortels
    """
    return session.run(query).single()["accidents_mortels"]


def get_total_usagers(session):
    query = """
    MATCH (u:Usager)
    RETURN COUNT(u) AS total_usagers
    """
    return session.run(query).single()["total_usagers"]




# Affichage de l'onglet "Accueil"
def accueil():

    st.write("Cette application analyse les accidents de la route en 2023, en étudiant les lieux, les véhicules et les usagers pour dégager des tendances clés.")

    session = get_neo4j_session()
    total_accidents = session.run("MATCH (a:Accident) RETURN count(a) AS total").single()["total"]
    accidents_mortels = get_accidents_mortels(session)
    total_usagers = get_total_usagers(session)

    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Total des Accidents en 2023", content=total_accidents)
    with cols[1]:
        ui.metric_card(title="Nombre d'accidents mortels", content=accidents_mortels)
    with cols[2]:
        ui.metric_card(title="Nombre total d'usagers impliqués", content=total_usagers)

    accidents_par_mois()


# Affichage de l'onglet "Accidents"
def accidents():

    st.markdown("## Analyse des Accidents")
    
    analyse_localisation()
    analyse_heure()
    analyse_climat()
    analyse_collision()
    
# Affichage de l'onglet "Véhicules"
def vehicules():

    st.markdown("## Analyse des Véhicules")

    analyse_categories_vehicules()
    analyse_obstacles()
   

# Affichage de l'onglet "Usagers"
def usagers():
    
    st.markdown("## Analyse des Usagers")

    usagers_sexe()
    usagers_gravite()
    analyse_ages_usagers()
    analyse_trajets_usagers()


# Affichage de l'onglet "Contact"
def contact():

    st.markdown("## Formulaire")

    st.write("Pour toute question ou assistance concernant notre application, contactez-nous via ce formulaire")

    contact_form = """ 
    <form action="https://formsubmit.co/faysalyameogo1@gmail.com" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="text" name="name" placeholder="Entrez votre nom" required>
        <input type="email" name="email" placeholder="Entrez votre email" required>
        <textarea name="message" placeholder="Message"></textarea>
        <button type="submit">Envoyer</button>
    </form>

    """
    st.markdown(contact_form, unsafe_allow_html=True)


    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    local_css("./Style/file.css")

#-------------------------------------
def run_gds_algorithm(algorithm, params):
    """
    Exécute un algorithme GDS sur la base Neo4j.
    """
    with driver.session() as session:
        query = f"""
        CALL gds.{algorithm}({params})
        YIELD *
        RETURN *
        """
        result = session.run(query)
        return [record.data() for record in result]

def gds_tab():
    """
    Ajoute un onglet pour exécuter des algorithmes de GDS sur les données.
    """
    st.title("Analyse Graph Data Science")
    st.write("Utilisez cette section pour exécuter des algorithmes de Data Science sur le graphe.")

    # Sélection de l'algorithme
    algo_choice = st.selectbox(
        "Choisissez un algorithme GDS",
        ["PageRank", "Shortest Path", "Node Similarity"]
    )

    # Paramètres automatiques basés sur le choix de l'algorithme
    if algo_choice == "PageRank":
        params = """
        {
            "nodeProjection": "Lieu",
            "relationshipProjection": {
                "A_LIEU": {
                    "type": "A_LIEU",
                    "orientation": "UNDIRECTED"
                }
            },
            "maxIterations": 20,
            "dampingFactor": 0.85
        }
        """
    elif algo_choice == "Shortest Path":
        start_node = st.text_input("Identifiant du lieu de départ", value="Lieu1")
        end_node = st.text_input("Identifiant du lieu de destination", value="Lieu2")
        params = f"""
        {{
            "startNode": gds.util.asNode('{start_node}'),
            "endNode": gds.util.asNode('{end_node}'),
            "nodeProjection": "Lieu",
            "relationshipProjection": {{
                "A_LIEU": {{
                    "type": "A_LIEU",
                    "orientation": "UNDIRECTED"
                }}
            }}
        }}
        """
    elif algo_choice == "Node Similarity":
        params = """
        {
            "nodeProjection": "Vehicule",
            "relationshipProjection": {
                "IMPLIQUE_A": {
                    "type": "IMPLIQUE_A",
                    "orientation": "UNDIRECTED"
                }
            },
            "similarityCutoff": 0.5,
            "degreeCutoff": 1
        }
        """
    
    # Bouton pour exécuter
    if st.button(f"Exécuter {algo_choice}"):
        try:
            results = run_gds_algorithm(algo_choice.lower(), params)
            st.success(f"Résultats de {algo_choice} :")
            st.json(results)
        except Exception as e:
            st.error(f"Erreur lors de l'exécution : {e}")

# Interface avec onglets
def main():

    st.sidebar.image("pro.png", use_container_width=True)

    st.title("Tableau de Bord des Accidents")
    
    selected_tab = ui.tabs(options=["Accueil", "Accidents", "Véhicules", "Usagers", "Contact","Data science"], default_value="Accueil", key="tabs")
    
    if selected_tab == "Accueil":
        accueil()
    elif selected_tab == "Accidents":
        accidents()
    elif selected_tab == "Véhicules":
        vehicules()
    elif selected_tab == "Usagers":
        usagers()
    elif selected_tab == "Contact":
        contact()
    elif selected_tab == "Data science":
        gds_tab()

if __name__ == "__main__":
    main()