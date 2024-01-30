import os
import PIL
from PIL.ExifTags import TAGS, GPSTAGS
import json


# nous renvoie les coordonées GPS d'une image
def GetExifCoordonates(image):
    """
    Cette fonction permet de récupérer les coordonées GPS d'une image en utilisant les données EXIF
    :param image: image dont on veut récupérer les coordonées GPS
    :return: lat: latitude, lng: longitude
    :rtype: float, float
    """
    exif = image._getexif()
    lat = 0.0
    lng = 0.0
    if exif:
        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gpsinfo = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gpsinfo[sub_decoded] = value[t]
                lat = ConvertToDegrees(gpsinfo["GPSLatitude"])
                if gpsinfo["GPSLatitudeRef"] != "N":
                    lat = 0 - lat
                lng = ConvertToDegrees(gpsinfo["GPSLongitude"])
                if gpsinfo["GPSLongitudeRef"] != "E":
                    lng = 0 - lng
    return lat, lng


def ConvertToDegrees(value):
    """
    Cette fonction permet de convertir les coordonées GPS en degrés décimaux
    :param value: coordonées GPS en degrés, minutes, secondes
    :return: coordonées GPS en degrés décimaux
    """
    d = value[0]
    m = value[1]
    s = value[2]
    return d + (m / 60.0) + (s / 3600.0)


def recuperation_images(dos_name=None):
    """
    Cette fonction permet de récupérer les liens des images dans le dossier static/images ainsi que le nom des dossiers
    :return: images: liste des liens des images, dos_name : liste des noms des dossiers
    :rtype: list, list
    """
    images = []
    if dos_name:
        file = "./static/images/" + dos_name + "/"
        for dos2 in os.listdir(file):
            if dos2.endswith(".jpg") or dos2.endswith(".png") or dos2.endswith(".JPG") or dos2.endswith(".PNG"):
                images.append(file + dos2)
        return images, dos_name


    dos_name = []
    for dos in os.listdir("./static/images/"):
        if dos != "desktop.ini":
            file = "./static/images/" + dos + "/"
            dos_name.append(dos)
            for dos2 in os.listdir(file):
                if dos2.endswith(".jpg") or dos2.endswith(".png") or dos2.endswith(".JPG") or dos2.endswith(".PNG"):
                    images.append(file + dos2)
    return images, dos_name


def integration_images_sqlite():
    """
    Cette fonction permet de créer les lignes de commandes SQL pour intégrer les images dans la base de données.
    :return: lignes_exec_sql : liste des commandes SQL deja formé pour être executées, dos_name: liste des noms des dossiers
    :rtype: list, list
    """
    images, dos_name = recuperation_images()
    lignes_exec_sql = []
    for i in range(len(images)):
        image = PIL.Image.open(images[i])
        lat, lng = GetExifCoordonates(image)
        if i % 2 == 0:
            ID_zone = int(i / 2) + 1
        else:
            ID_zone = int((i - 1) / 2) + 1
        ID_photo = i+1  # images[i].split("/")[-1]
        lignes_exec_sql.append(
            "INSERT OR REPLACE INTO TRESOR (LAT, LONG, ID_ZONE, ID_PHOTO) VALUES (" + str(round(lat, 9)) + ", " +
            str(round(lng, 9)) + ", " + str(ID_zone) + ", " + str(ID_photo) + ");")
    return lignes_exec_sql, dos_name


def recuperation_json():
    """
    Cette fonction permet de récupérer les liens des json et geojson dans le dossier static/images
    :return: geojson : liste des liens des geojson et json, dos_name : liste des noms des dossiers
    :rtype: list, list.
    """
    geojson = []
    nom_eleve = []
    for dos in os.listdir("./static/images/"):
        if dos != "desktop.ini":
            file = "./static/images/" + dos + "/"
            nom_eleve.append(dos)
            for dos in os.listdir(file):
                if dos.endswith(".json") or dos.endswith(".JSON") or dos.endswith(".geojson") or dos.endswith(".GEOJSON"):
                    geojson.append(file + dos)
    return geojson, nom_eleve


def recherche_donnee_json(geojson):
    """
    Cette fonction permet de récupérer les données du geojson.
    :type geojson: Object
    :param geojson: liens vers le geojson ou le json
    :return: nom_zone: nom de la zone, coordonnees : coordonnées de la zone
    :rtype: list, list
    """
    liens_json = geojson
    with open(liens_json, "r", encoding='utf-8') as fichier:
        data = json.load(fichier)

    nom_zone = []
    coordonnees = []

    for n in range(len(data["features"])):
        nom_zone.append(data["features"][n]["properties"]["zone_name"])
        tmps = []
        for i in range(len(data["features"][n]["geometry"]["coordinates"][0])):
            tmps.append(data["features"][n]["geometry"]["coordinates"][0][i])
            tmps[i][0] = round(tmps[i][0], 7)
            tmps[i][1] = round(tmps[i][1], 7)
        coordonnees.append(tmps)
    return nom_zone, coordonnees


def integration_json_sqlite():
    """
    Cette fonction permet de créer les lignes de commandes SQL pour intégrer les données du json dans la base de données.
    :return lignes_exec_sql : liste des commandes SQL deja formé pour être executées
    :rtype: list
    """
    lignes_exec_sql = []
    geojson, nom_eleve = recuperation_json()
    u = 1
    for i in range(len(geojson)):
        nom_zone, coordonnees = recherche_donnee_json(geojson[i])
        nombre_tresor = 0
        etudiant = nom_eleve[i]
        for j in range(len(nom_zone)):
            if "'" in nom_zone[j]:
                nom_zone[j] = nom_zone[j].replace("'", "''")
            lignes_exec_sql.append("INSERT OR REPLACE INTO ZONE (ZONE, NOM, COORDONNEES, NOMBRE_TRESOR, ETUDIANT) "
                                   "VALUES (" + str(u) + ", '" + nom_zone[j] + "', '" + str(coordonnees[j]) + "', " +
                                   str(nombre_tresor) + ", '" + etudiant + "');")
            u += 1
    return lignes_exec_sql
