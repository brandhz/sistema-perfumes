import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json
import os

# --- CONFIGURAÇÃO INICIAL ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass 

st.set_page_config(page_title="Zeidan Parfum System", layout="wide")

# --- LOGIN SIMPLES ---
senha = st.sidebar.text_input("🔒 Senha de Acesso", type="password")
if senha != "12041995": 
    st.info("Digite a senha para acessar.")
    st.stop()

# --- CONEXÃO COM GOOGLE SHEETS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        if "CREDENCIAIS_JSON" in st.secrets:
            info_json = st.secrets["CREDENCIAIS_JSON"]
            creds_dict = json.loads(info_json, strict=False)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            
            # Conecta direto, sem avisos na tela
            NOME_PLANILHA = "Controle Zeidan Parfum"
            return client.open(NOME_PLANILHA)
            
        else:
            st.error("❌ ERRO: Secrets 'CREDENCIAIS_JSON' sumiu.")
            return None

    except Exception as e:
        st.error(f"❌ Erro de Conexão: {e}")
        st.markdown(f"1. Verifique se o nome da planilha no Google é **exatamente** `Controle Zeidan Parfum`.")
        return None

# --- FUNÇÕES ÚTEIS ---
def pegar_hora_brasil():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso)

def limpar_numero(valor):
    if not valor: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor = str(valor).replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0

def _ler_dados_brutos(sheet, nome_aba, colunas_esperadas):
    try:
        worksheet = sheet.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        # Cria a aba silenciosamente se não existir
        worksheet = sheet.add_worksheet(title=nome_aba, rows=100, cols=20)
        worksheet.append_row(colunas_esperadas)
    
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
    return df, worksheet

# --- INÍCIO DO APP ---
st.title("📦 Sistema Zeidan Parfum")

sheet = conectar_google_sheets()

if sheet is None:
    st.stop()

# --- CARREGAMENTO DE DADOS ---
cols_prod = ["ID", "Produto", "Custo_Padrao", "Preco_Venda"]
cols_comp = ["Pedido", "Data", "Data_Chegada", "ID", "Produto", "Qtd", "Custo_Unit", "Fornecedor", "Status", "Observacoes"]
cols_vend = ["Pedido", "ID", "Produto", "Status", "Custo", "Preco_Tabela", "Lucro_Dif", "Valor_Recebido", "Margem_Perc", "Data", "Plataforma", "Ponto_de_Contato", "Observacoes"]

try:
    df_produtos, _ = _ler_dados_brutos(sheet, "Produtos", cols_prod)
    df_compras, _ = _ler_dados_brutos(sheet, "Compras", cols_comp)
    df_vendas, _ = _ler_dados_brutos(sheet, "Vendas", cols_vend)
except Exception as e:
    st.error(f"Erro crítico ao ler abas: {e}")
    st.stop()

# --- MENU LATERAL ---
menu = st.sidebar.radio("Menu", ["Vender", "Comprar", "Cadastrar Produto", "Relatórios"])

def gerar_id_venda(df_vendas):
    if df_vendas is None or df_vendas.empty or "Pedido" not in df_vendas.columns: return "ZP01"
    try:
        lista = [x for x in df_vendas["Pedido"] if str(x).startswith("ZP")]
        if not lista: return "ZP01"
        ultimo = lista[-1]
        numero = int(str(ultimo).replace("ZP", ""))
        return f"ZP{numero + 1:02d}"
    except: return "ZP??"

def gerar_id_compra(df_compras):
    if df_compras is None or df_compras.empty or "Pedido" not in df_compras.columns: return "CP01"
    try:
        lista = [x for x in df_compras["Pedido"] if str(x
