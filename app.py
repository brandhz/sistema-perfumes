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

# ==========================================
# 🚨 ÁREA DE DIAGNÓSTICO (RODA NO TOPO) 🚨
# ==========================================
try:
    st.divider()
    st.markdown("### 🕵️ Diagnóstico de Conexão")
    
    if "CREDENCIAIS_JSON" in st.secrets:
        # 1. Tenta ler quem é o robô
        info = json.loads(st.secrets["CREDENCIAIS_JSON"], strict=False)
        email_robo = info.get("client_email", "Não encontrado")
        st.info(f"🤖 **O Robô é:** `{email_robo}`")
        st.caption("👆 Copie este e-mail e verifique se ele está como EDITOR na planilha.")

        # 2. Tenta conectar no Google Drive para listar arquivos
        scope_diag = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_diag = ServiceAccountCredentials.from_json_keyfile_dict(info, scope_diag)
        client_diag = gspread.authorize(creds_diag)
        
        # Tenta listar as planilhas que ele vê
        lista = client_diag.list_spreadsheet_files()
        
        if not lista:
            st.error("🚫 O robô conectou, mas não vê NENHUMA planilha.")
            st.warning("⚠️ PROVÁVEL CAUSA: Você precisa ativar a 'Google Drive API' no console do Google Cloud.")
        else:
            encontrei = False
            st.write("📂 **Planilhas que eu consigo ver:**")
            for arq in lista:
                st.write(f"- 📄 {arq['name']} (ID: `{arq['id']}`)")
                # Verifica se é a planilha certa (pelo ID do Zeidan)
                if "1q5pgZ3OEpJhFjdbZ19xp1k2dUWzXhPL16SRMZNWaV-k" in arq['id']:
                    encontrei = True
            
            if encontrei:
                st.success("✅ SUCESSO! O robô tem acesso à sua planilha!")
            else:
                st.warning("⚠️ O robô vê algumas planilhas, mas NÃO a do Zeidan Parfum. Verifique o compartilhamento.")
    else:
        st.error("❌ ERRO: Não encontrei 'CREDENCIAIS_JSON' nos Secrets!")

    st.divider()

except Exception as e:
    # Se der erro aqui, é porque a API está desligada ou o JSON está errado
    st.error(f"❌ O diagnóstico falhou. Erro: {e}")
    st.warning("DICA: Verifique se ativou 'Google Sheets API' e 'Google Drive API' no Google Cloud.")

# ==========================================
# 🏁 FIM DO DIAGNÓSTICO - INÍCIO DO APP 🏁
# ==========================================

# --- FUNÇÃO DE SEGURANÇA ---
def pegar_segredo(chave):
    if chave in st.secrets:
        return st.secrets[chave]
    return os.getenv(chave)

# --- LOGIN ---
senha_secreta = pegar_segredo("SENHA_ACESSO")
if not senha_secreta:
    st.error("ERRO CRÍTICO: Senha não configurada! Verifique os 'Secrets'.")
    st.stop()

senha = st.sidebar.text_input("🔒 Senha de Acesso", type="password")
if senha != str(senha_secreta):
    st.warning("Por favor, digite a senha para acessar o sistema.")
    st.stop()

# --- URL DA PLANILHA ---
URL_PLANILHA = pegar_segredo("LINK_DA_PLANILHA")

# --- CONEXÃO COM GOOGLE SHEETS (BLINDADA) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds = None
        
        # 1. Tenta pegar do BLOCO JSON nos Secrets
        if "CREDENCIAIS_JSON" in st.secrets:
            info_json = st.secrets["CREDENCIAIS_JSON"]
            creds_dict = json.loads(info_json, strict=False)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # 2. Fallback: Tenta pegar arquivo local
        elif os.path.exists("zeidan-parfum.json"):
             creds = ServiceAccountCredentials.from_json_keyfile_name("zeidan-parfum.json", scope)
        
        if creds:
            client = gspread.authorize(creds)
            # TENTA ABRIR PELO ID (Mais seguro contra erro 404)
            try:
                # Tenta extrair o ID se for link completo
                if "/d/" in URL_PLANILHA:
                    id_planilha = URL_PLANILHA.split("/d/")[1].split("/")[0]
                    return client.open_by_key(id_planilha)
                else:
                    return client.open_by_url(URL_PLANILHA)
            except Exception:
                # Se falhar a extração, tenta abrir direto
                return client.open_by_url(URL_PLANILHA)
        else:
            return None

    except Exception as e:
        st.error(f"❌ Erro de Conexão Detalhado: {e}")
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

# --- CARREGAMENTO DE DADOS ---
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
        st.error(f"Erro ao ler abas: {e
