import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Zeidan Parfum System", layout="wide")

# --- SENHA DE PROTEÇÃO (PIN) ---
# Como o repo é público, isso impede estranhos de mexerem
senha = st.sidebar.text_input("🔒 Senha de Acesso", type="password")
if senha != "130712":
    st.warning("Por favor, digite a senha para acessar o sistema.")
    st.stop()

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

# --- CONEXÃO BLINDADA (AUTO-REPAIR) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # Tenta ler do Cofre de Segredos (Streamlit Secrets)
        if "gcp_service_account" in st.secrets:
            # Pega o texto do JSON
            info_json = st.secrets["gcp_service_account"]["json_key"]
            
            # Converte texto em dicionário
            creds_dict = json.loads(info_json)
            
            # --- CORREÇÃO AUTOMÁTICA DE QUEBRA DE LINHA ---
            # Se a chave privada veio 'colada' errada, isso conserta:
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open_by_url(URL_PLANILHA)
        else:
            st.error("❌ Erro: Configure o segredo [gcp_service_account] no painel do Streamlit.")
            return None
            
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

if sheet is None:
    st.stop() # Para o app aqui se não conectar

if df_produtos is None:
    st.warning("⚠️ Conectado, mas não consegui ler os produtos.")
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
            
            # DATA BRASILEIRA
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
                margem = (lucro / val) if val > 0 else 0
                sheet.worksheet("Vendas").append_row([
                    ped, id_sel, dados["Produto"], stat, cus, limpar_numero(dados["Preco_Venda"]),
                    lucro, val, f"{margem:.2%}", dt.strftime("%d/%m/%Y"), plat, cli, obs
                ])
                st.success("✅ Venda Registrada!")
                st.cache_data.clear()
                st.rerun()

# ================= COMPRAR =================
elif menu == "Comprar":
    st.header("🛒 Nova Compra")
    opcoes = df_produtos["ID"] + " - " + df_produtos["Produto"]
    selecao = st.selectbox("Item", opcoes) if not df_produtos.empty else None
    sugestao = gerar_id_compra(df_compras)

    if selecao:
        id_sel = selecao.split(" - ")[0]
        dados = df_produtos.loc[df_produtos["ID"] == id_sel].iloc[0]
        
        with st.form("compra"):
            c1, c2, c3 = st.columns(3)
            ped = c1.text_input("Pedido", value=sugestao)
            
            # DATAS BRASILEIRAS
            dt = c2.date_input("Data Pedido", pegar_hora_brasil(), format="DD/MM/YYYY")
            cheg = c3.date_input("Previsão Chegada", pegar_hora_brasil(), format="DD/MM/YYYY")
            
            c4, c5 = st.columns(2)
            qtd = c4.number_input("Qtd", 1)
            custo = c5.number_input("Custo Unit", value=limpar_numero(dados["Custo_Padrao"]))
            
            c6, c7 = st.columns(2)
            forn = c6.selectbox("Fornecedor", ["Niche House", "Baroni Parfum", "Flowers", "Outro"])
            stat = c7.selectbox("Status", ["Pedido Feito", "Aprovado", "Enviado", "Entregue"])
            
            obs = st.text_input("Obs")
            
            if st.form_submit_button("Registrar Compra"):
                sheet.worksheet("Compras").append_row([
                    ped, dt.strftime("%d/%m/%Y"), cheg.strftime("%d/%m/%Y"),
                    id_sel, dados["Produto"], qtd, custo, forn, stat, obs
                ])
                st.success("✅ Compra Registrada!")
                st.cache_data.clear()
                st.rerun()

# ================= CADASTRAR =================
elif menu == "Cadastrar Produto":
    st.header("✨ Novo Produto")
    with st.form("new_prod"):
        id_n = st.text_input("ID (Código)")
        nome = st.text_input("Nome do Perfume")
        c1, c2 = st.columns(2)
        custo = c1.number_input("Custo Padrão", 0.0)
        venda = c2.number_input("Preço Venda", 0.0)
        
        if st.form_submit_button("Salvar Produto"):
            if id_n and nome:
                sheet.worksheet("Produtos").append_row([id_n, nome, custo, venda])
                st.success("✅ Produto Criado!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Preencha ID e Nome!")

# ================= RELATÓRIOS =================
elif menu == "Relatórios":
    st.header("📊 Painel Gerencial")
    tab1, tab2 = st.tabs(["Vendas", "Compras"])
    
    with tab1:
        if df_vendas is not None and not df_vendas.empty:
            df_vendas['Data_Obj'] = pd.to_datetime(df_vendas['Data'], format='%d/%m/%Y', errors='coerce')
            mes_atual = pegar_hora_brasil().month
            vendas_mes = df_vendas[df_vendas['Data_Obj'].dt.month == mes_atual]
            
            if not vendas_mes.empty:
                total_mes = vendas_mes["Valor_Recebido"].apply(limpar_numero).sum()
                st.metric(f"Faturamento Mês {mes_atual}", f"R$ {total_mes:,.2f}")
            
            st.dataframe(df_vendas.drop(columns=['Data_Obj'], errors='ignore'), hide_index=True, use_container_width=True)
        else: st.info("Sem histórico de vendas.")
        
    with tab2:
        if df_compras is not None and not df_compras.empty:
            st.dataframe(df_compras, hide_index=True, use_container_width=True)
        else: st.info("Sem histórico de compras.")
