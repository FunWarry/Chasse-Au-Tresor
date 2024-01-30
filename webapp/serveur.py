# Gevraise Mathéo ESEO E2
# Projet de fin d'année
#
# Ce programme permet de créer une carte interactive avec des flêches qui indique la direction à prendre pour trouver
# le trésor Il permet aussi de créer une base de données avec les coordonées GPS des trésors et de les afficher sur
# la carte


from flask import Flask, render_template, redirect, url_for, request

import folium
import math

import sqlite3
import os

import photos_json_tretement as pjt

import Py_tresor as pt

import itertools

app = Flask(__name__)
app.config["DEBUG"] = True


def angle_between_points(point1, point2):
    """
    Cette fonction permet de calculer l’angle des fleches après analyse, je me suis rendu compte que cela ne pouvais
    pas marcher, car la Terre est ronde avec des coordonnées sphériques.
    :param point2: Coordonnés GPS point d’arrivée
    :param point1: Coordonnés GPS point de départ
    :type point1: tuple, list
    :type point2: tuple, list
    :return: angle entre les deux points
    :rtype: float
    """
    x1, y1 = point1
    x2, y2 = point2
    y = round(y2 - y1, 7)
    x = round(x2 - x1, 7)
    res = math.degrees(math.atan2(y, x))
    distance = distance_between_points(point1, point2)
    # partie ajustement de la rotation des fleches
    if x < 0:
        res += 38
        if y < 0:
            res -= 8
    else:
        res += 22
        if y < 0:
            res += 20

    return res


def distance_between_points(point1, point2):
    """
    Cette fonction permet de calculer la distance entre deux points
    :param point1:  Coordonnés GPS point de départ
    :param point2:  Coordonnés GPS point d’arrivée
    :return:  distance entre les deux points
    :rtype: float
    """
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# renvois les résultats des requêtes SQL sous forme de dictionnaire
def dict_factory(cursor, row):
    """
    :param cursor:  curseur de la base de données
    :param row:  ligne de la base de données
    :return:  dictionnaire avec les noms des colonnes comme clés
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# regarder si un fichier existe ou non et le créer si besoin
if not os.path.exists("./static/bdd_projet.sqlite"):
    conn = sqlite3.connect('./static/bdd_projet.sqlite')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS TRESOR
                (
                LAT      FLOAT NOT NULL CHECK (LAT BETWEEN -90 AND 90),
                LONG     FLOAT NOT NULL CHECK (LONG BETWEEN -180 AND 180),
                ID_ZONE  INT  NOT NULL,
                ID_PHOTO INT  NOT NULL,
                PRIMARY KEY (ID_PHOTO),
                FOREIGN KEY (ID_ZONE) REFERENCES ZONE(ZONE)
                )"""
                )

    cur.execute("""CREATE TABLE IF NOT EXISTS ZONE
                (
                ZONE          INT           NOT NULL,
                NOM           CHAR          NOT NULL,
                COORDONNEES   FLOAT         NOT NULL,
                NOMBRE_TRESOR INT           NOT NULL,
                ETUDIANT      CHAR          NOT NULL,
                PRIMARY KEY (ZONE)
                )"""
                )

    conn.commit()

    lignes_exec_tresor, dos_name = pjt.integration_images_sqlite()
    lignes_exec_zone = pjt.integration_json_sqlite()
    cur = conn.cursor()
    for i in range(len(lignes_exec_tresor)):
        cur.execute(lignes_exec_tresor[i])
    for i in range(len(lignes_exec_zone)):
        cur.execute(lignes_exec_zone[i])
    conn.commit()
    conn.close()

print("Le serveur est lancé")


def create_map(name, zone=any):
    """
    Cette fonction permet de créer la carte avec les trésors et les flêches
    :param name:  nom de la personne a qui on souhaite chercher le trésor
    :type name: str
    :param zone:  afficher les zones ?
    :type zone: bool
    :return:  la carte avec les trésors et les flêches
    :rtype: folium.Map
    """
    # recuperation des données de la base de données
    connexion = sqlite3.connect('./static/bdd_projet.sqlite')
    connexion.row_factory = dict_factory
    cursor = connexion.cursor()
    data_bdd = cursor.execute(
        "SELECT * FROM TRESOR INNER JOIN ZONE Z on Z.ZONE = TRESOR.ID_ZONE WHERE ETUDIANT = ?;", (name,)).fetchall()
    connexion.close()

    # création de la carte
    new_map = folium.Map()

    # ajout des zones polygonales avec les coordonnées dans la base de données
    if zone == None:
        for index in range(0, len(data_bdd), 2):
            data = data_bdd[index]["COORDONNEES"].replace("[", "").replace("]", "").split(",")
            data = [float(i) for i in data]
            data = [data[i:i + 2] for i in range(0, len(data), 2)]
            for i in range(len(data)):
                data[i][0], data[i][1] = data[i][1], data[i][0]
            pop = folium.Popup(f"Nom de zone : {data_bdd[index]['NOM']}", max_width=200)
            folium.Polygon(data, color="red", fill_color="red", fill_opacity=0.1, popup=pop).add_to(new_map)

    # ajout des trésors
    coordonnees_tresor_selectionne_old = []

    numero_image = []  # liste des niméro des images pour le joueur

    id_image = []  # liste des id des images pour le joueur

    id_zone = []  # liste des id des zones pour le joueur

    def dat(data_bdd, tresor):
        """
        Cette fonction permet de récupérer les données de la base de données
        évite les doublons
        :param data_bdd:  données de la base de données
        :param tresor:  numéro d'incrément
        :return: les données de la base de données
        :rtype: list
        """
        val_increment = tresor
        numero_image.append(tresor)
        id_zone.append(data_bdd[tresor]["NOM"])
        id_image.append(data_bdd[tresor]["ID_PHOTO"])
        return val_increment, numero_image, id_zone, id_image

    for tresor in range(0, len(data_bdd), 2):
        if data_bdd[tresor]["NOMBRE_TRESOR"] % 2 == 0:
            val_increment, numero_image, id_zone, id_image = dat(data_bdd, tresor)
        else:
            val_increment, numero_image, id_zone, id_image = dat(data_bdd, tresor + 1)

        # ajout des coordonnées des trésors dans une liste
        coordonnees_tresor_selectionne_old.append([data_bdd[val_increment]["LAT"], data_bdd[val_increment]["LONG"]])

    # relier les strésors par les lignes droites en faisant le trajet le plus cours
    coordonnees_tresor_selectionne = trajet_plus_court(coordonnees_tresor_selectionne_old)

    image, dos_name = pjt.recuperation_images(name)

    # recupère l'indice du nouvel ordre des trésors
    indice = []
    for i in range(len(coordonnees_tresor_selectionne)):
        for j in range(len(coordonnees_tresor_selectionne_old)):
            if coordonnees_tresor_selectionne[i] == coordonnees_tresor_selectionne_old[j]:
                indice.append(j)

    # trier la liste des images selectionnées dans l'ordre des indices
    image_order = [image[numero_image[i]] for i in indice]
    id_zone_order = [id_zone[i] for i in indice]
    id_image_order = [id_image[i] for i in indice]

    # pointeur
    for tresor in range(len(coordonnees_tresor_selectionne)):
        icon = folium.features.CustomIcon('./static/pin.png', icon_size=(30, 40), icon_anchor=(15, 40))
        popup = folium.Popup(folium.Html("Id zone : " + str(id_zone_order[tresor]) + "<br>"
                                         + "Id image : " + str(id_image_order[tresor]) + "<br>"
                                         + "Latitude : " + str(coordonnees_tresor_selectionne[tresor][0]) + "<br>"
                                         + "Longitude : " + str(coordonnees_tresor_selectionne[tresor][1]) + "<br>"
                                         + f"""<img src="{image_order[tresor]}" height="150">""", script=True), max_width=2650)
        folium.Marker(coordonnees_tresor_selectionne[tresor], icon=icon, popup=popup).add_to(new_map)

    # ajout des flêches
    for tresor in range(len(coordonnees_tresor_selectionne) - 1):
        color = "yellow" if tresor == 0 else "blue"
        folium.RegularPolygonMarker(coordonnees_tresor_selectionne[tresor], number_of_sides=3, radius=15,
                                    fill_color=color,
                                    fill_opacity=1,
                                    rotation=angle_between_points(coordonnees_tresor_selectionne[tresor],
                                                                  coordonnees_tresor_selectionne[tresor + 1])).add_to(
            new_map)
    # cercle d'arrivée
    folium.RegularPolygonMarker(coordonnees_tresor_selectionne[-1], number_of_sides=80, radius=10, fill_color='red',
                                fill_opacity=1).add_to(new_map)

    # tracer les lignes
    folium.PolyLine(coordonnees_tresor_selectionne, color="black", weight=2.5, opacity=1).add_to(new_map)

    return new_map


def trajet_plus_court(coords):
    # Génère toutes les permutations possibles des coordonnées
    permutations = itertools.permutations(coords)
    # Initialise la distance minimale à l'infini
    distance_min = float('inf')
    # Initialise la permutation correspondant au trajet le plus court à None
    trajet_plus_court = None
    # Pour chaque permutation, calcule la distance totale parcourue
    for trajet in permutations:
        distance_totale = 0
        for i in range(len(trajet) - 1):
            distance_totale += distance_between_points(trajet[i], trajet[i + 1])
        # Si la distance totale est plus courte que la distance minimale, met à jour la distance minimale et le
        # trajet le plus court.
        if distance_totale < distance_min:
            distance_min = distance_totale
            trajet_plus_court = trajet
    # Retourne le trajet le plus court
    return trajet_plus_court


lignes_exec_tresor, dos_name = pjt.integration_images_sqlite()

new_value = []
for i in range(len(dos_name)):
    var_sep = dos_name[i].split(" ")
    new_value.append(str(var_sep[0] + var_sep[1]))

print("Images traitées dans la base de données")

element_selection = "Mathéo Gevraise"


@app.route("/", methods=('POST', 'GET'))
def home():
    if request.method == 'POST':

        screen_size = request.form.get('screen_size')

        element_selection = request.form['joueurs']

        zone = request.form.get('affichage_zone')

        for i in range(len(dos_name)):
            if element_selection == new_value[i]:
                element_selection = dos_name[i]
                break

        m = create_map(element_selection, zone)
        m.fit_bounds(m.get_bounds(), padding=(40, 40))
        return render_template("HTML-joueurs.html", map=m._repr_html_(), nom_personnes=dos_name,
                               nmbr_joueurs=len(dos_name), element=element_selection, new_value=new_value)
    else:
        element_selection = "Mathéo Gevraise"
        m = create_map("Mathéo Gevraise", None)
        m.fit_bounds(m.get_bounds(), padding=(40, 40))
        return render_template("HTML-joueurs.html", map=m._repr_html_(), nom_personnes=dos_name,
                               nmbr_joueurs=len(dos_name), element=element_selection, new_value=new_value)


def recuperation_essential_value(element_selection):
    """
    Eviter des éléments dupliqués
    :param element_selection:
    :return image_name: ID des images
    :return zone_name: ID des zones
    :return map_coroplet: carte coroplet

    """
    dict_id = pt.recup_nom_zone_photo(element_selection)
    image_name = []
    zone_name = []
    for key, value in dict_id.items():
        image_name.append(value)
        zone_name.append(key)

    json, trash = pjt.recuperation_json()
    del trash
    map_coroplet = pt.creation_carte_coroplet(json)

    return image_name, zone_name, map_coroplet


@app.route("/tresor/<element_selection>", methods=('GET', 'POST'))
def tresor(element_selection):
    if request.method == 'POST':

        tresor_selection = request.form['select_immages']
        zone_selected = int(tresor_selection.split("_")[-1])

        pt.tresor_trouve(zone_selected, element_selection)

        image_name, zone_name, map_coroplet = recuperation_essential_value(element_selection)

        return render_template("HTML-tresor.html", image_name=image_name, zone_name=zone_name,
                               map=map_coroplet._repr_html_(),
                               nom_personnes=dos_name, nmbr_joueurs=len(dos_name), element=element_selection,
                               new_value=new_value)
    else:
        image_name, zone_name, map_coroplet = recuperation_essential_value(element_selection)

        return render_template("HTML-tresor.html", image_name=image_name, zone_name=zone_name,
                               map=map_coroplet._repr_html_(),
                               nom_personnes=dos_name, nmbr_joueurs=len(dos_name), new_value=new_value)


app.run()
