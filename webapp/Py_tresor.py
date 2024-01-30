import sqlite3
import os
import folium
import pandas as pd
import json as js


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


def tresor_trouve(ZONE_ID, name):
    """
    Cette fonction permet de modifier la base de donnée en fonction du trésor trouvé
    :param ZONE_ID: id du trésor trouvé
    :type ZONE_ID: int
    :param name: nom de l'étudiant
    :type name: str
    :return: None
    :rtype: None
    """
    connexion = sqlite3.connect('./static/bdd_projet.sqlite')
    connexion.row_factory = dict_factory
    cursor = connexion.cursor()
    data_bdd = cursor.execute(
        "SELECT * FROM TRESOR INNER JOIN ZONE Z on Z.ZONE = TRESOR.ID_ZONE WHERE ETUDIANT = ?;", (name,)).fetchall()

    new_data_bdd = []
    for i in range(0, len(data_bdd[0]), 2):
        new_data_bdd.append(data_bdd[i])

    new_id_zone = int(ZONE_ID) + new_data_bdd[0]["ZONE"]

    data_change = new_data_bdd[ZONE_ID]["NOMBRE_TRESOR"] + 1

    cursor.execute(
        f"UPDATE ZONE SET NOMBRE_TRESOR = {data_change} WHERE ZONE = {new_id_zone};").fetchall()

    connexion.commit()
    connexion.close()


def recup_nom_zone_photo(name):
    """
    Cette fonction permet de récupérer les noms des zones et les id des photos
    :param name: nom de l'étudiant
    :return: dictionnaire avec les noms des zones comme clés et les id des photos comme valeurs
    :rtype: dict
    """
    connexion = sqlite3.connect('./static/bdd_projet.sqlite')
    connexion.row_factory = dict_factory
    cursor = connexion.cursor()
    data_bdd = cursor.execute(
        "SELECT * FROM TRESOR INNER JOIN ZONE Z on Z.ZONE = TRESOR.ID_ZONE WHERE ETUDIANT = ?;", (name,)).fetchall()
    connexion.close()

    new_data_bdd = []
    for i in range(0, len(data_bdd[0]), 2):
        new_data_bdd.append(data_bdd[i])

    returned_data = {}
    for i in range(len(new_data_bdd)):
        returned_data[new_data_bdd[i]["NOM"]] = new_data_bdd[i]["ID_PHOTO"]

    return returned_data


def creation_carte_coroplet(json):
    """
    Cette fonction permet de créer la carte complète avec toutes les zones
    :return: la carte complète
    :rtype: folium.Map
    """
    connexion = sqlite3.connect('./static/bdd_projet.sqlite')
    connexion.row_factory = dict_factory
    cursor = connexion.cursor()

    data_bdd = cursor.execute(
        "SELECT ZONE, COORDONNEES, NOMBRE_TRESOR FROM ZONE;").fetchall()

    data_used = pd.read_sql("SELECT ZONE, NOMBRE_TRESOR FROM ZONE;", con=connexion, columns=['ZONE', 'NOMBRE_TRESOR'])


    connexion.close()

    for i in range(len(data_bdd[0])):
        data_bdd[i]["COORDONNEES"] = data_bdd[i]["COORDONNEES"].replace("[", "").replace("]", "").split(",")
        data_bdd[i]["COORDONNEES"] = [float(j) for j in data_bdd[i]["COORDONNEES"]]
        data_bdd[i]["COORDONNEES"] = [data_bdd[i]["COORDONNEES"][j:j + 2] for j in
                                      range(0, len(data_bdd[i]["COORDONNEES"]), 2)]
        for j in range(len(data_bdd[i]["COORDONNEES"])):
            data_bdd[i]["COORDONNEES"][j][0], data_bdd[i]["COORDONNEES"][j][1] = int(data_bdd[i]["COORDONNEES"][j][1]), \
                int(data_bdd[i]["COORDONNEES"][j][0])

    fusion_json(json, data_bdd)

    county_path = os.path.join(os.getcwd(), 'static/geojson.json')
    new_json = js.load(open(county_path))

    map_coroplet = folium.Map(location=[47.449682, -0.486366], zoom_start=12, tiles='cartodbpositron', control_scale=True, )

    folium.Choropleth(
        geo_data=new_json,
        name='choropleth',
        data=data_used,
        key_on='feature.properties.zone_id',
        columns=['ZONE', 'NOMBRE_TRESOR'],
        fill_color="YlGnBu",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Nombre de trésors trouvé',
        reset=True
    ).add_to(map_coroplet)

    folium.LayerControl().add_to(map_coroplet)

    return map_coroplet


def fusion_json(list_json, donnees_bdd):
    """
    Cette fonction permet de fusionner les json en un seul en utilisant une bibliothèque python (json)
    :param list_json: liste des json
    :type list_json: list
    :param donnees_bdd: données de la base de données
    :type donnees_bdd: list
    :return: le json fusionné
    :rtype: dict.
    """
    new_json = {"type": "FeatureCollection", "features": []}
    for index in list_json:
        fichier_actuel = js.load(open(index))
        for i in fichier_actuel["features"]:
            new_json["features"].append(i)
    for i in range(len(donnees_bdd)):
        new_json["features"][i]["properties"]["zone_id"] = donnees_bdd[i]["ZONE"]

    with open("./static/geojson.json", "w") as f:
        js.dump(new_json, f)

    return new_json
