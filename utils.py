"""
Funciones dentro de este archivo:
1. validar_id_carpeta(texto) - Tomar una cadena de texto y validar si es un id válido para una carpeta en Google Drive
2. validar_dataframes(dict_dfs) - Tomar un diccionario y validar si sus valores son dataframes
3. validar_nombre_excel(nombre) - Tomar el nombre de un archivo y validar si tiene una extensión válida de Excel
4. ajustar_columnas(df, sufijo) - Agregar sufijo a todas las columnas de un dataframe para que se distingan en los cruces
"""

import re
import pandas as pd

def validar_id_carpeta(texto):
    """
    Tomar una cadena de texto y validar si es un id válido para una carpeta en Google Drive
    Args:
    - texto         (str)   -   texto que se desea validar
    Return
    - id_valido     (bool)  -   validación si es un id válido o no
    """
    if re.match(r"^[a-zA-Z0-9_-]{25,}$", texto):
        id_valido = True
    else:
        id_valido = False
    return id_valido

def validar_dataframes(dict_dfs: dict):
    """
    Tomar un diccionario y validar si sus valores son dataframes
    Args:
    - dict_dfs          (dict)  - diccionario con los nombres de las hojas y los dataframes asociados
    Return:
    - valores_validos   (bool)  - validación si los valores del diccionario son dataframes válidos
    """
    
    for k, v in dict_dfs.items():
        if not isinstance(v, pd.DataFrame):
            valores_validos = False
        else:
            valores_validos = True
    
    return valores_validos

def validar_nombre_excel(nombre: str):
    """
    Tomar el nombre de un archivo y validar si tiene una extensión válida de Excel
    Args:
    - nombre                (str)   - nombre para validar
    Return
    - nombre_valido         (bool)  - validación si el nombre de excel es permitido
    """
    if re.match(r"^[^\\\/:*?\"<>|]+(?:\.xlsx)$", nombre):
        nombre_valido = True
    else:
        nombre_valido = False

    return 
    
def ajustar_columnas(df, sufijo):
  """
  Agregar sufijo a todas las columnas de un dataframe para que se distingan en los cruces
  Args:
  - df    pd.DataFrame
  Return:
  - df    pd.DataFrame
  """
  for col in df.columns:
    if col == "identificacion":
      continue
    df.rename(columns={col: f"{col}_{sufijo}"}, inplace=True)
  return df

