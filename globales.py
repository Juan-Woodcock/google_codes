#%%
#Importar las librerías necesarias para interactuar con Drive
import gspread
from google.auth import default
from google.cloud import bigquery
creds, _ = default()
gc = gspread.authorize(creds)

#Importar las librerías básicas para manipulación de datos
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import re

#Importar librerías adicionales
import os
import locale
import time
import warnings
from json import dumps
from httplib2 import Http
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

#Importar funciones de apoyo
from utils import *

#Algunas configuraciones adicionales
pd.set_option('display.max_columns', None)
pd.options.display.float_format = '{:,.2f}'.format
locale.setlocale(locale.LC_ALL, "")

warnings.filterwarnings('ignore')

#%%
#Definición de las funciones
def enviar_alerta_hangouts(texto):
  """
  Tomar un mensaje y enviar una alerta a Hangouts
  Args:
  - texto:    (str)     Texto a enviar
  """
  url="https://chat.googleapis.com/v1/spaces/AAAAxU9SPPM/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=InAHVjSPGFdL-vkmGma-fyXtYzXgHTcN2IL9vncJSpo"
  bot_message = {
      "text": texto
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
      uri=url,
      method="POST",
      headers=message_headers,
      body=dumps(bot_message),
  )

def cargar_excel_a_drive(dict_dfs: dict, id_carpeta: str, nombre_archivo: str):
    """
    Tomar una lista de pandas dataframes y guardarlos en un archivo de Excel en una carpeta de
    Google Drive especificada por su id.

    Args:
    - dict_dfs              (dict)  -   diccionario con los nombres de las hojas en que se guardarán los dataframes:
                                            * llaves:   (str)           - nombre de la hoja
                                            * valores:  (pd.DataFrame)  - dataframe que se desea cargar en la hoja correspondiente
    - id_carpeta            (str)   -   id de la carpeta en Drive en que se guardará el archivo de Excel
    - nombre_archivo        (str)   -   nombre con que se guardará el archivo de Excel en Drive
    """
    #Validar los tipos de datos
    if not isinstance(dict_dfs, dict):
        raise ValueError("El parámetro 'dict_dfs' no corresponde a un diccionario.")
    
    #Validar el id de la carpeta
    if validar_id_carpeta(id_carpeta) == False:
        raise ValueError("El parámetro 'id_carpeta' no corresponde a una carpeta válida en Drive.")

    #Validar que los datos en el diccionario sean válidos
    if validar_dataframes(dict_dfs) == False:
        raise ValueError("Las llaves del diccionario ingresado no son dataframes válidos.")

    #Validar que el nombre para el archivo de Excel sea válido
    if validar_nombre_excel(nombre_archivo) == False:
        raise ValueError("El nombre para el archivo de Excel no es válido.")

    #Crear un Excel Writer
    ruta_temp = f"/tmp/{nombre_archivo}"
    with pd.ExcelWriter(ruta_temp, engine="openpyxl") as writer:
        for nombre_hoja, df in dict_dfs.items():
            df.to_excel(writer, sheet_name=nombre_hoja, index=False)

    #Autenticarse y crear el cliente de Drive
    creds, _ = default()
    drive_service = build("drive", "v3", credentials=creds)

    #Crear y montar el objeto (archivo)
    metadata = {
        "name": nombre_archivo,
        "parents": [id_carpeta]
    }

    media = MediaFileUpload(ruta_temp, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    #Montar el archivo en la carpeta de Drive
    archivo = drive_service.files().create(body=metadata, media_body=media, fields='id').execute()
    id_archivo = archivo.get("id")

    #Mostrar el mensaje de éxito
    print(f"Los dataframes fueron cargados en el archivo {nombre_archivo} con id {id_archivo} en la carpeta {id_carpeta}.")
    return id_archivo


def cargar_excel_desde_drive(id_archivo: str, nombre_hoja: str = None):
    """
    Cargar la información de una hoja de un archivo de Excel ubicado en Google Drive.
    Args:
    - id_archivo        (str)               id del archivo de Excel en Google Drive
    - nombre_hoja       (str)               nombre de la hoja de donde se traerá la información
    Return:             
    - df                (pd.DataFrame)      dataframe con la información de la hoja de Excel
    """

    #Autenticarse y crear el cliente de Drive
    creds, _ = default()
    drive_service = build("drive", "v3", credentials=creds)

    #Descargar el archivo de Excel
    try:
        request = drive_service.files().get_media(fileId=id_archivo)
        contenido = io.BytesIO(request.execute())
    except:
        raise ValueError("No se pudo leer el archivo del ID especificado.")

    #Leer la hoja especificada
    if nombre_hoja:
        df = pd.read_excel(contenido, sheet_name=nombre_hoja, dtype=str)
    else:
        df = pd.read_excel(contenido, dtype=str)

    return df

def cargar_desde_sheets(id: int, hoja: int):
    '''
    Carga la información de un Google Sheets y una hoja específica a un dataframe
    Args:
        - id      (str):          id de la hoja de Sheets
        - hoja    (str):          nombre de la pestaña
    Returns:
        - df      (pd.dataframe): dataframe con la información de Sheets
    '''

    ss = gc.open_by_key(id)
    ss = ss.worksheet(hoja).get_all_values()
    df = pd.DataFrame(ss[1:], columns=ss[0])

    return df

def cargar_a_sheets(df, id, hoja, rango="A1", reemplazo=True):
    '''
    Cargar la información de un dataframe a un Google Sheets en una hoja específica.
    Por defecto, el rango se pegará en el rango A1
    Args:
        - id      (str)           id de la hoja en que se cargará el dataframe
        - df      (pd.DataFrame)  dataframe que desea ser cargado en sheets
        - hoja    (str)           hoja en que se cargará el dataframe
        - rango   (str)           rango en que se cargará el dataframe. Debe ser en notación A1
    '''
    df = df.astype(str)
    workbook = gc.open_by_key(id)
    if reemplazo == True:
        workbook.worksheet(hoja).clear()
    hoja_rango = '{}!{}'.format(hoja, rango)
    workbook.values_update(
        hoja_rango,
        params={
            'valueInputOption': 'USER_ENTERED'
        },
        body={
            'values':[df.columns.values.tolist()] + df.values.tolist()
        }
    )

def cargar_a_bigquery(project_id, dataset_id, table_name, df):
    """
    Tomar un dataframe y cargarlo a una tabla en BigQuery.
    Si la tabla ya existe, la reemplaza
    Args:
    - project_id  (str):
    - dataset_id  (str):
    - table_name  (str):
    - df          (pd.DataFrame):
    """

    client = bigquery.Client(project=project_id)

    table_ref = client.dataset(dataset_id).table(table_name)
    try:
        client.get_table(table_ref)
        client.delete_table(table_ref)
        print(f"Table {table_name} already exists")
    except:
        pass

    table = bigquery.Table(table_ref)
    table = client.create_table(table)

    job_config = bigquery.LoadJobConfig()
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    print(job.result())

def cargar_desde_bigquery(query, project_id):
    """
    Crear una consulta en BigQuery y almacenar los resultados en un dataframe
    Args:
    - query       (str): consulta
    - project_id  (str): id del proyecto en bigquery
    Return:
    - df          (pd.DataFrame): dataframe con la información del query
    """
    client = bigquery.Client(project=project_id)
    query_job = client.query(query)
    df = query_job.to_dataframe()
    return df

def crear_sheets(id_carpeta, nombre_archivo=None, nombres_hojas=None):
    """
    Crear un archivo de Google Sheets en una carpeta específica.
    Al nuevo archivo se le actualizarán los nombres de las hojas.
    Args:
    - id_carpeta (str):     ID de la carpeta en Google Drive.
    - nombre_archivo (str): Nombre del archivo.
    - nombres_hojas (list): Nombres de las hojas.
    Returns:
    - id_archivo (str):     ID del archivo en Google Drive.
    """
    #Autenticarse y crear el cliente de Drive
    creds, _ = default()
    drive_service = build("drive", "v3", credentials=creds)

    #Crear la metadata del archivo
    metadata = {
        "name": nombre_archivo,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [id_carpeta]
    }

    #Crear el archivo y obtener su id
    archivo = drive_service.files().create(body=metadata, fields="id").execute()
    id_archivo = archivo.get("id")

    #Actualizar los nombres de las hojas
    if nombres_hojas:
        archivo = gc.open_by_key(id_archivo)
        for i in range(len(nombres_hojas)):
            if i == 0:
                hoja = archivo.get_worksheet(0)
                hoja.update_title(nombres_hojas[i])
            else:
                archivo.add_worksheet(title=nombres_hojas[i], rows="1000", cols="26")

    return id_archivo

def cargar_plano_desde_drive(id_archivo: str, separador: str = ",", encabezado: int = 0):
    """
    Cargar la información de un archivo plano separado ubicado en Google Drive. Toda la información es importada como texto plano
    Args:
    - id_archivo        (str)               id del archivo plano en Google Drive
    - separador         (str)               separador del archivo plano. Por defecto, ","
    Return:             
    - df                (pd.DataFrame)      dataframe con la información del archivo plano
    """

    #Autenticarse y crear el cliente de Drive
    creds, _ = default()
    drive_service = build("drive", "v3", credentials=creds)

    #Descargar el archivo plano
    try:
        request = drive_service.files().get_media(fileId=id_archivo)
        contenido = io.BytesIO(request.execute())
        #Leer el archivo plano
        df = pd.read_csv(contenido, sep=separador, encoding='unicode-escape', header=encabezado, dtype=str)
        return df
    except:
        raise ValueError("No se pudo leer el archivo del ID especificado.")

def cargar_plano_a_drive(df, nombre_archivo, id_carpeta):
    """
    Tomar un pandas dataframe y guardarlo en una carpeta de google drive como un archivo de texto plano.

    Args:
    - df:               (pd.DataFrame)  - dataframe que se desea guardar
    - nombre_archivo:   (str)           - nombre para el archivo de texto plano
    - id_carpeta:       (str)           - id de la carpeta en google drive
    Return:
    - id_archivo:       (str)           - id del archivo creado en google drive
    """
    # Guarda el DataFrame como un archivo CSV localmente
    ruta_temp = f"/tmp/{nombre_archivo}"
    df.to_csv(ruta_temp, index=False)

    #Autenticarse y crear el cliente de Drive
    creds, _ = default()
    drive_service = build("drive", "v3", credentials=creds)

    #Crear y montar el objeto (archivo)
    metadata = {
        "name": nombre_archivo,
        "parents": [id_carpeta]
    }

    media = MediaFileUpload(ruta_temp, mimetype='text/csv')

    #Montar el archivo en la carpeta de Drive
    archivo = drive_service.files().create(body=metadata, media_body=media, fields='id').execute()
    id_archivo = archivo.get("id")

    #Mostrar el mensaje de éxito
    print(f"Los dataframes fueron cargados en el archivo {nombre_archivo} con id {id_archivo} en la carpeta {id_carpeta}.")
    return id_archivo