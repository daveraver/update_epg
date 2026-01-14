import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Configuració
URL_EPG = "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiafanart_sincolor1.xml.gz"
FITXER_LOCAL = "epg_historic.xml.gz"
DIES_HISTORIC = 7

def descarregar_i_descomprimir(url):
    r = requests.get(url)
    return gzip.decompress(r.content)

def parsejar_data_xml(data_str):
    # El format XMLTV sol ser: 20240520060000 +0200
    return datetime.strptime(data_str[:14], "%Y%m%d%H%M%S")

def actualitzar_epg():
    print("Iniciant actualització de l'EPG...")
    
    # 1. Obtenir dades noves
    contingut_nou = descarregar_i_descomprimir(URL_EPG)
    root_nou = ET.fromstring(contingut_nou)
    
    # 2. Carregar històric existent o crear-ne un de nou
    if os.path.exists(FITXER_LOCAL):
        with gzip.open(FITXER_LOCAL, 'rb') as f:
            root_historic = ET.parse(f).getroot()
    else:
        root_historic = ET.Element("tv")
        # Copiar atributs del root (generator, etc)
        for k, v in root_nou.attrib.items():
            root_historic.set(k, v)

    # 3. Crear diccionari d'esdeveniments existents per evitar duplicats
    # Clau: (id_canal, hora_inici)
    existents = set()
    for prog in root_historic.findall('programme'):
        existents.add((prog.get('channel'), prog.get('start')))

    # 4. Afegir programes nous que no estiguin a l'històric
    canals_nous = root_nou.findall('channel')
    programes_nous = root_nou.findall('programme')
    
    # Actualitzar llista de canals (per si n'hi ha de nous)
    ids_canals_hist = [c.get('id') for c in root_historic.findall('channel')]
    for canal in canals_nous:
        if canal.get('id') not in ids_canals_hist:
            root_historic.append(canal)

    for prog in programes_nous:
        clau = (prog.get('channel'), prog.get('start'))
        if clau not in existents:
            root_historic.append(prog)

    # 5. Purgar programes de fa més de 7 dies
    limit_temps = datetime.now() - timedelta(days=DIES_HISTORIC)
    
    per_eliminar = []
    for prog in root_historic.findall('programme'):
        data_fi = parsejar_data_xml(prog.get('stop'))
        if data_fi < limit_temps:
            per_eliminar.append(prog)
    
    for prog in per_eliminar:
        root_historic.remove(prog)

    # 6. Guardar el fitxer resultant comprimit
    xml_string = ET.tostring(root_historic, encoding='utf-8', xml_declaration=True)
    with gzip.open(FITXER_LOCAL, 'wb') as f:
        f.write(xml_string)
    
    print(f"Procés finalitzat. Fitxer '{FITXER_LOCAL}' actualitzat.")

if __name__ == "__main__":
    actualitzar_epg()
