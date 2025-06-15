# Google Sheets Integration with Python on macOS using Google Cloud CLI

This guide walks you through setting up your macOS environment to write to Google Sheets using Python, **without downloading JSON credentials**. It uses `gcloud` CLI and `application-default login` for authentication.

---

## ⚙️ Setup

### 1. Install Google Cloud SDK

```bash
sudo ./google-cloud-sdk/install.sh
```

### 2. Initialize gcloud and set correct permissions

```bash
sudo gcloud init
```

```bash
sudo chown -R "$(whoami)" ~/.config/gcloud
```

During this process:
- Sign in via browser
- Set your default Google Cloud project
- Install any prompted dependencies

### 3. Authenticate to access Google Sheets & Drive APIs

```bash
gcloud auth application-default login \
--scopes=https://www.googleapis.com/auth/cloud-platform,\
https://www.googleapis.com/auth/spreadsheets,\
https://www.googleapis.com/auth/drive
```

---

## 🧪 Python Environment

### 1. Set up a virtual environment

```bash
python -m venv .venv
```  
```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### `requirements.txt`

```plain
google-api-python-client==2.172.0
pandas==2.2.3
ipykernel==6.29.5
google-genai==1.18.0
python-dotenv==1.1.0
openpyxl==3.1.5
google-auth==2.40.3
google-api-core==2.25.1
google-auth-httplib2==0.2.0
python-dotenv==1.1.0
```

---

## 🧾 Python Code to Upload DataFrame to Google Sheets

```python
import os
import numpy as np
import pandas as pd
from google.auth import default
from googleapiclient.discovery import build
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

ID = os.environ.get("ID")
SHEET_NAME = os.environ.get("SHEET_NAME")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds, _ = default(scopes=SCOPES)
svc = build("sheets", "v4", credentials=creds)

def cargar_a_sheets(df, sheet_id, hoja, rango="A1", reemplazo=True):
    df = df.astype(str)
    body = {"values": [df.columns.tolist()] + df.values.tolist()}

    if reemplazo:
        svc.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range=hoja
        ).execute()

    svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{hoja}!{rango}",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

np.random.seed(42)

data = {
    "EmployeeID": np.arange(1001, 1011),
    "Name": [f"Employee_{i}" for i in range(1, 11)],
    "Department": np.random.choice(["Sales", "Engineering", "HR", "Marketing"], size=10),
    "Salary": np.random.randint(50000, 120000, size=10),
    "HireDate": pd.date_range(start="2015-01-01", periods=10, freq="365D"),
    "FullTime": np.random.choice([True, False], size=10)
}

df = pd.DataFrame(data)

cargar_a_sheets(df=df, sheet_id=ID, hoja=SHEET_NAME, reemplazo=False)
```

## Alternative Python code: `cargar_a_sheets()` using the `gspread` library
```python
import os
import numpy as np
import pandas as pd
from google.auth import default

# Same constants as before

#Authenticate to access Google Sheets & Drive APIs
creds, _ = default(scopes=SCOPES)
gc = gspread.authorize(creds)

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

cargar_a_sheets(df=df, id=ID, hoja=SHEET_NAME, reemplazo=False)
```