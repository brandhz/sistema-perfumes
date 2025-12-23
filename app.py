import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json  # Importante para ler o segredo!

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Zeidan Parfum System", layout="wide")

# 🔗 SUA URL DA PLANILHA
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

# --- CONEXÃO BLINDADA (LÊ DO COFRE OU DO ARQUIVO) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 1. Tenta ler do Cofre de Segredos (Streamlit Cloud)
        if "gcp_service_account" in st.secrets:
            info_json = st.secrets["gcp_service_account"]["json_key"]
            creds_dict = json.loads(info_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # 2. Se não achar no cofre, tenta ler arquivo local (PC)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
            
        client = gspread.authorize(creds)
        return client.open_by_url(URL_PLANILHA)
        
    except Exception as e:
        st.error(f"❌ Erro Crítico de Conexão: {e}")
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
        return df, worksheet
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=nome_aba, rows=100, cols=20)
        worksheet.append_row(colunas_esperadas)
        return pd.DataFrame(columns=colunas_esperadas), worksheet

# --- CARREGAMENTO ---
@st.cache_data(ttl=10)
def carregar_dados_cache():
    sheet = conectar_google_sheets()
    if not sheet: return None, None, None
    
    cols_prod = ["ID", "Produto", "Custo_Padrao", "Preco_Venda"]
    cols_comp = ["Pedido", "Data", "Data_Chegada", "ID", "Produto", "Qtd", "Custo_Unit", "Fornecedor", "Status", "Observacoes"]
    cols_vend = ["Pedido", "ID", "Produto", "Status", "Custo", "Preco_Tabela", "Lucro_Dif", "Valor_Recebido", "Margem_Perc", "Data", "Plataforma", "Ponto_de_Contato", "Observacoes"]
    
    try:
        df_p, _ = _ler_dados_brutos(sheet, "Produtos", cols_prod)
        df_c, _ = _ler_dados_brutos(sheet, "Compras", cols_comp)
        df_v, _ = _ler_dados_brutos(sheet, "Vendas", cols_vend)
        return df_p, df_c, df_v
    except Exception as e:
        st.error(f"Erro ao ler abas: {e}")
        return None, None, None

# --- GERADORES DE CÓDIGO ---
def gerar_id_venda(df_vendas):
    if df_vendas is None or df_vendas.empty or "Pedido" not in df_vendas.columns: return "ZP01"
    try:
        ultimo = df_vendas["Pedido"].iloc[-1]
        numero = int(str(ultimo).replace("ZP", ""))
        return f"ZP{numero + 1:02d}"
    except: return "ZP??"

def gerar_id_compra(df_compras):
    if df_compras is None or df_compras.empty or "Pedido" not in df_compras.columns: return "CP01"
    try:
        lista = [x for x in df_compras["Pedido"] if str(x).startswith("CP")]
        if not lista: return "CP01"
        numero = int(str(lista[-1]).replace("CP", ""))
        return f"CP{numero + 1:02d}"
    except: return "CP??"

# --- INÍCIO DO APP ---
st.title("📦 Sistema Zeidan Parfum")

sheet = conectar_google_sheets()
df_produtos, df_compras, df_vendas = carregar_dados_cache()

if sheet is None or df_produtos is None:
    st.warning("⚠️ Aguardando conexão...")
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("Menu", ["Vender", "Comprar", "Cadastrar Produto", "Relatórios"])

# ================= VENDER =================
if menu == "Vender":
    st.header("💰 Nova Venda")
    opcoes = df_produtos["ID"] + " - " + df_produtos["Produto"]
    selecao = st.selectbox("Produto", opcoes) if not df_produtos.empty else None
    sugestao = gerar_id_venda(df_vendas)

    if selecao:
        id_sel = selecao.split(" - ")[0]
        dados = df_produtos.loc[df_produtos["ID"] == id_sel].iloc[0]
        
        with st.form("venda"):
            c1, c2, c3, c4 = st.columns(4)
            ped = c1.text_input("Pedido", value=sugestao)
            
            # DATA DD/MM/AAAA
            dt = c2.date_input("Data", pegar_hora_brasil(), format="DD/MM/YYYY")
            
            stat = c3.selectbox("Status", ["Entregue", "Pendente", "Enviado"])
            plat = c4.selectbox("Canal", ["Pessoalmente", "Instagram", "WhatsApp"])
            
            c5, c6 = st.columns(2)
            val = c5.number_input("Valor Venda", value=limpar_numero(dados["Preco_Venda"]))
            cus = c6.number_input("Custo", value=limpar_numero(dados["Custo_Padrao"]))
            
            c7, c8 = st.columns(2)
            cli = c7.text_input("Cliente")
            obs = c8.text_input("Obs")
            
            if st.form_submit_button("Confirmar Venda"):
                lucro = val - cus
                margem
