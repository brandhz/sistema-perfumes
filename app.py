import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Zeidan Parfum System", layout="wide")

# ⚠️ COLE AQUI A URL DA SUA PLANILHA ⚠️
URL_PLANILHA = "COLE_SUA_URL_AQUI"

# --- FUNÇÃO FAXINEIRA (LIMPA NÚMEROS) ---
def limpar_numero(valor):
    if not valor: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0

# --- CONEXÃO ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
        client = gspread.authorize(creds)
        return client.open_by_url(URL_PLANILHA)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
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
    
    # CORREÇÃO AQUI: Retorna apenas 3 Nones se falhar
    if not sheet: return None, None, None 
    
    cols_prod = ["ID", "Produto", "Custo_Padrao", "Preco_Venda"]
    
    cols_comp = [
        "Pedido", "Data", "Data_Chegada", "ID", 
        "Produto", "Qtd", "Custo_Unit", 
        "Fornecedor", "Status", "Observacoes"
    ]
    
    cols_vend = [
        "Pedido", "ID", "Produto", "Status", 
        "Custo", "Preco_Tabela", "Lucro_Dif", "Valor_Recebido", 
        "Margem_Perc", "Data", "Plataforma", "Ponto_de_Contato", "Observacoes"
    ]
    
    df_p, _ = _ler_dados_brutos(sheet, "Produtos", cols_prod)
    df_c, _ = _ler_dados_brutos(sheet, "Compras", cols_comp)
    df_v, _ = _ler_dados_brutos(sheet, "Vendas", cols_vend)
    
    return df_p, df_c, df_v

# --- GERADORES DE CÓDIGO (ZP e CP) ---
def gerar_id_venda(df_vendas):
    if df_vendas.empty or "Pedido" not in df_vendas.columns: return "ZP01"
    try:
        ultimo = df_vendas["Pedido"].iloc[-1]
        numero = int(str(ultimo).replace("ZP", ""))
        return f"ZP{numero + 1:02d}"
    except: return "ZP??"

def gerar_id_compra(df_compras):
    if df_compras.empty or "Pedido" not in df_compras.columns: return "CP01"
    try:
        # Pega o último que tenha CP (ignora vazios)
        lista_cps = [x for x in df_compras["Pedido"] if str(x).startswith("CP")]
        if not lista_cps: return "CP01"
        ultimo = lista_cps[-1]
        numero = int(str(ultimo).replace("CP", ""))
        return f"CP{numero + 1:02d}"
    except: return "CP??"

# --- INÍCIO DO APP ---
sheet = conectar_google_sheets()
df_produtos, df_compras, df_vendas = carregar_dados_cache()

st.title("📦 Sistema Zeidan Parfum")

if sheet is None: st.stop()

# --- MENU ---
menu = st.sidebar.radio("Menu", ["Vender", "Comprar", "Cadastrar Produto", "Relatórios"])

# ==============================================================================
# 🛒 COMPRAR (AGORA COM DROPDOWN E NOVAS COLUNAS)
# ==============================================================================
if menu == "Comprar":
    st.header("🛒 Nova Compra (Entrada)")
    
    opcoes_prod = df_produtos["ID"] + " - " + df_produtos["Produto"]
    selecao = st.selectbox("Selecione o Item", opcoes_prod) if not df_produtos.empty else None
    
    sugestao_cp = gerar_id_compra(df_compras)

    if selecao:
        id_sel = selecao.split(" - ")[0]
        dados_prod = df_produtos.loc[df_produtos["ID"] == id_sel].iloc[0]
        nome_produto = dados_prod["Produto"]
        custo_padrao = limpar_numero(dados_prod["Custo_Padrao"])
        
        with st.form("compra"):
            st.caption(f"📦 Produto: {nome_produto}")
            
            # Linha 1: Dados Básicos
            c1, c2, c3 = st.columns(3)
            cod_pedido = c1.text_input("Cód. Pedido", value=sugestao_cp)
            data_compra = c2.date_input("Data do Pedido", datetime.now())
            data_chegada = c3.date_input("Previsão Chegada", datetime.now())
            
            # Linha 2: Valores e Qtd
            c4, c5 = st.columns(2)
            qtd = c4.number_input("Quantidade", 1)
            custo = c5.number_input("Custo Unitário (R$)", value=custo_padrao, format="%.2f")
            
            # Linha 3: Fornecedor e Status (COM DROPDOWN!)
            c6, c7 = st.columns(2)
            # Adicione aqui os seus fornecedores
            lista_fornecedores = ["Niche House", "Baroni Parfum", "Flowers", "Outro"]
            fornecedor = c6.selectbox("Fornecedor", lista_fornecedores)
            
            # Adicione aqui os status de compra
            lista_status = ["Pedido Feito", "Aprovado", "Enviado", "Entregue", "Cancelado"]
            status = c7.selectbox("Status", lista_status)
            
            # Linha 4: Obs
            obs = st.text_input("Observações")
            
            # Formata datas
            d_compra_str = data_compra.strftime("%d/%m/%Y")
            d_chegada_str = data_chegada.strftime("%d/%m/%Y")
            
            if st.form_submit_button("📥 Registrar Compra"):
                ws = sheet.worksheet("Compras")
                # Salva na ordem EXATA da sua planilha nova
                ws.append_row([
                    cod_pedido,      # A: Pedido
                    d_compra_str,    # B: Data
                    d_chegada_str,   # C: Data_Chegada
                    id_sel,          # D: ID
                    nome_produto,    # E: Produto
                    qtd,             # F: Qtd
                    custo,           # G: Custo_Unit
                    fornecedor,      # H: Fornecedor
                    status,          # I: Status
                    obs              # J: Observacoes
                ])
                st.success(f"Compra {cod_pedido} registrada!")
                st.cache_data.clear()
                st.rerun()

# ==============================================================================
# 💰 VENDER
# ==============================================================================
elif menu == "Vender":
    st.header("💰 Nova Venda")
    
    opcoes_prod = df_produtos["ID"] + " - " + df_produtos["Produto"]
    sugestao_zp = gerar_id_venda(df_vendas)
    
    selecao = st.selectbox("Produto", options=opcoes_prod) if not df_produtos.empty else None
    
    if selecao:
        id_sel = selecao.split(" - ")[0]
        dados_prod = df_produtos.loc[df_produtos["ID"] == id_sel].iloc[0]
        preco_padrao = limpar_numero(dados_prod["Preco_Venda"])
        custo_padrao = limpar_numero(dados_prod["Custo_Padrao"])
        
        with st.form("form_venda"):
            c1, c2, c3, c4 = st.columns(4)
            cod_pedido = c1.text_input("Pedido", value=sugestao_zp)
            data_venda = c2.date_input("Data", datetime.now())
            status = c3.selectbox("Status", ["Entregue", "Pendente", "Enviado"])
            plataforma = c4.selectbox("Canal", ["Pessoalmente", "Instagram", "WhatsApp"])
            
            c5, c6 = st.columns(2)
            valor_recebido = c5.number_input("Valor Recebido", value=preco_padrao, format="%.2f")
            custo_momento = c6.number_input("Custo", value=custo_padrao, format="%.2f")
            
            c7, c8 = st.columns(2)
            cliente = c7.text_input("Cliente")
            obs = c8.text_input("Obs")
            
            if st.form_submit_button("✅ Confirmar"):
                lucro = valor_recebido - custo_momento
                margem = (lucro / valor_recebido) if valor_recebido > 0 else 0
                
                sheet.worksheet("Vendas").append_row([
                    cod_pedido, id_sel, dados_prod['Produto'], status,
                    custo_momento, preco_padrao,
                    lucro, valor_recebido, f"{margem:.2%}",
                    data_venda.strftime("%d/%m/%Y"), plataforma, cliente, obs
                ])
                st.success("Venda Salva!")
                st.cache_data.clear()
                st.rerun()

# ==============================================================================
# 📦 CADASTRAR PRODUTO
# ==============================================================================
elif menu == "Cadastrar Produto":
    st.header("✨ Novo Produto")
    with st.form("prod"):
        c1, c2 = st.columns(2)
        id_n = c1.text_input("ID")
        nome = c2.text_input("Nome")
        c3, c4 = st.columns(2)
        custo = c3.number_input("Custo", 0.0)
        venda = c4.number_input("Venda", 0.0)
        
        if st.form_submit_button("Salvar"):
            sheet.worksheet("Produtos").append_row([id_n, nome, custo, venda])
            st.success("Salvo!")
            st.cache_data.clear()
            st.rerun()

# ==============================================================================
# 📊 RELATÓRIOS
# ==============================================================================
elif menu == "Relatórios":
    st.title("📊 Painel Gerencial")
    
    tab_vendas, tab_compras = st.tabs(["💰 Vendas", "🛒 Compras"])
    
    with tab_vendas:
        if not df_vendas.empty:
            # Cálculos rápidos
            df_vendas["V_Real"] = df_vendas["Valor_Recebido"].apply(limpar_numero)
            df_vendas["L_Real"] = df_vendas["Lucro_Dif"].apply(limpar_numero)
            
            k1, k2 = st.columns(2)
            k1.metric("Faturamento", f"R$ {df_vendas['V_Real'].sum():,.2f}")
            k2.metric("Lucro", f"R$ {df_vendas['L_Real'].sum():,.2f}")
            
            st.dataframe(df_vendas.drop(columns=["V_Real", "L_Real"]), hide_index=True, use_container_width=True)
        else:
            st.info("Sem vendas.")

    with tab_compras:
        if not df_compras.empty:
            # Tratamento para totais
            df_compras["Qtd_Num"] = pd.to_numeric(df_compras["Qtd"], errors='coerce').fillna(0)
            df_compras["Custo_Num"] = df_compras["Custo_Unit"].apply(limpar_numero)
            df_compras["Total"] = df_compras["Qtd_Num"] * df_compras["Custo_Num"]
            
            st.metric("Total Investido", f"R$ {df_compras['Total'].sum():,.2f}")
            
            # Mostra colunas principais
            cols_show = ["Pedido", "Data", "Produto", "Qtd", "Custo_Unit", "Fornecedor", "Status", "Total"]
            # Filtra colunas que realmente existem para não dar erro
            cols_existentes = [c for c in cols_show if c in df_compras.columns]
            
            st.dataframe(df_compras[cols_existentes], hide_index=True, use_container_width=True)
        else:
            st.info("Sem compras.")