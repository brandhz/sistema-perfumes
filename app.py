import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Zeidan Parfum System", layout="wide")

# 🔗 SUA URL
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1q5pgZ3OEpJhFjdbZ19xp1k2dUWzXhPL16SRMZnWaV-k/edit?gid=1032083161#gid=1032083161"

# --- FUNÇÕES ÚTEIS ---
def pegar_hora_brasil():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso)

def limpar_numero(valor):
    if not valor: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0

# --- CONEXÃO BLINDADA (VIA SECRETS) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 1. Tenta ler do Cofre de Segredos (Streamlit Cloud)
        if "gcp_service_account" in st.secrets:
            info_json = st.secrets["gcp_service_account"]["json_key"]
            creds_dict = json.loads(info_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # 2. Fallback: Se não achar no cofre, tenta ler arquivo local (PC)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
            
        client = gspread.authorize(creds)
        return client.open_by_url(URL_PLANILHA)
        
    except Exception as e:
        st.error(f"❌ Erro de Conexão: {e}")
        return None

def _ler_dados_brutos(sheet, nome_aba, colunas_esperadas):
    try:
        worksheet = sheet.worksheet(nome_aba)
        dados = worksheet.get_all_records()
        df = pd.DataFrame(dados)
        if df.empty:
            df = pd.DataFrame(columns=colunas_esperadas)
        else:
            for col in colunas_esperadas:
                if col not in df.columns:
                    df[col] = ""
            if "ID" in df.columns:
                df["ID"] = df["ID"].astype(str)
