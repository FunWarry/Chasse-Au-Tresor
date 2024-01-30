# se programe a pour but d'afficher toute les photos du dossier static/images sur une map avec toutes les zones, et chaque zone a une couleur qui sera associer a ces deux photos

# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 10:38:00 2020
"""
import sqlite3
import folium
import webbrowser
import photos_json_tretement as pjt


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


def recu_info():
    """
    Cette fonction permet de récupérer les informations de la base de données
    :return: dictionnaire avec les noms des zones comme clés et les id des photos comme valeurs
    :rtype: dict
    """
    connexion = sqlite3.connect('./static/bdd_projet.sqlite')
    connexion.row_factory = dict_factory
    cursor = connexion.cursor()
    data_bdd = cursor.execute(
        "SELECT * FROM TRESOR inner join ZONE Z on Z.ZONE = TRESOR.ID_ZONE;").fetchall()
    connexion.close()
    return data_bdd



image_link, dos_nam = pjt.recuperation_images()

m = folium.Map()

r=0

data = recu_info()

couleur = ["red", "blue", "green", "purple", "orange"]

for index in range(len(data) // 2):
    data = recu_info()
    zone_name = data[index * 2]["NOM"]
    data = data[index * 2]["COORDONNEES"].replace("[", "").replace("]", "").split(",")
    data = [float(i) for i in data]
    data = [data[i:i + 2] for i in range(0, len(data), 2)]
    for i in range(len(data)):
        data[i][0], data[i][1] = data[i][1], data[i][0]
    folium.Polygon(data, color="red", fill_color=couleur[index % 5], fill_opacity=0.5, popup=zone_name).add_to(m)

data = recu_info()


for i in range(65):
    couleur_app = couleur[i%5]
    for j in range(2):
        popup = image_link[r].split("/")[-1]
        folium.Marker(
            location=[data[r]["LAT"], data[r]["LONG"]],
            popup=f"{data[i*2+j]['ID_PHOTO']} u{i} {popup} {data[i*2+j]['LAT']} {data[i*2+j]['LONG']}",
            icon=folium.Icon(color=couleur[(i+1) % 5 - 1], icon='info-sign')
        ).add_to(m)
        r += 1


m.save("map.html")
webbrowser.open("map.html")

