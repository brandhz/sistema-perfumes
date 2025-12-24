import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum Store", page_icon="💎", layout="wide")

# --- CSS PERSONALIZADO (SUA IDENTIDADE VISUAL) ---
st.markdown("""
<style>
    /* 1. Fundo Geral do Site (Azul Escuro Profundo) */
    .stApp {
        background-color: #162d48;
        color: #FFFFFF;
    }
    
    /* Ajuste para inputs de texto (barra de busca) */
    .stTextInput > div > div > input {
        color: #162d48;
        background-color: #d2d2d2;
    }

    /* 2. Cartão do Produto (Azul Médio) */
    .product-card {
        background-color: #233e58;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #162d48; /* Borda sutil */
        transition: transform 0.2s, border-color 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Efeito ao passar o mouse */
    .product-card:hover {
        transform: scale(1.02);
        border-color: #d2d2d2; /* Borda Cinza Claro ao passar o mouse */
    }
    
    /* Título do Produto */
    .prod-title {
        font-size: 18px;
        font-weight: 600;
        margin: 10px 0;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF; /* Branco */
    }
    
    /* Preço */
    .price-tag {
        font-size: 24px;
        color: #d2d2d2; /* Cinza Claro (Destaque) */
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    /* Botão do WhatsApp (Verde padrão para reconhecimento, mas estilizado) */
    a.zap-btn {
        display: inline-block;
        width: 100%;
        padding: 12px;
        background-color: #25D366; 
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        transition: background-color 0.3s;
    }
    a.zap-btn:hover {
        background-color: #128C7E;
    }
    
    /* Divisor */
    hr {
        border-color: #d2d2d2;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "CREDENCIAIS_JSON" in st.secrets:
            info_json = st.secrets["CREDENCIAIS_JSON"]
            creds_dict = json.loads(info_json, strict=False)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("Controle Zeidan Parfum")
        else:
            return None
    except:
        return None

# --- CARREGAR DADOS ---
@st.cache_data(ttl=60)
def carregar_catalogo():
    sheet = conectar_google_sheets()
    if not sheet: return pd.DataFrame()
    try:
        ws = sheet.worksheet("Produtos")
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        cols_necessarias = ["Produto", "Preco_Venda"]
        for col in cols_necessarias:
            if col not in df.columns:
                return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# --- CABEÇALHO COM LOGO ---
c1, c2 = st.columns([1, 4])
with c1:
    # Tenta carregar a logo local, se não tiver usa ícone
    # Certifique-se de que o nome do arquivo no GitHub é logo.png ou logo.jpg
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/4003/4003733.png", width=80) 
        
with c2:
    st.title("Zeidan Parfum")
    st.markdown(f"<span style='color: #d2d2d2;'>A essência da elegância.</span>", unsafe_allow_html=True)

st.markdown("---")

# --- CARREGA DADOS ---
df = carregar_catalogo()

if df.empty:
    st.warning("⏳ Carregando catálogo...")
    st.button("🔄 Atualizar")
    st.stop()

# --- BUSCA ---
busca = st.text_input("🔍 O que você procura?", placeholder="Digite o nome do perfume...")
if busca:
    df = df[df["Produto"].astype(str).str.contains(busca, case=False)]

st.markdown("<br>", unsafe_allow_html=True)

# --- VITRINE ---
df = df[df["Preco_Venda"] != ""] # Remove produtos sem preço

cols = st.columns(3)

for index, row in df.iterrows():
    c_index = index % 3
    with cols[c_index]:
        # Imagem do produto
        img_url = row.get("Imagem", "")
        if not str(img_url).startswith("http"):
            img_url = "https://cdn-icons-png.flaticon.com/512/3050/3050253.png"

        # Preço
        preco = str(row['Preco_Venda']).replace("R$", "").strip()
        
        # WhatsApp Link
        msg = f"Olá! Vi o *{row['Produto']}* no site por R$ {preco} e tenho interesse."
        msg_encoded = msg.replace(" ", "%20")
        
        # --- ATENÇÃO: COLOQUE SEU NÚMERO AQUI ---
        TEL_ZEIDAN = "5531999999999" 
        link_zap = f"https://wa.me/{TEL_ZEIDAN}?text={msg_encoded}"

        # Card HTML
        st.markdown(f"""
        <div class="product-card">
            <img src="{img_url}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 10px;">
            <div class="prod-title">{row['Produto']}</div>
            <div class="price-tag">R$ {preco}</div>
            <a href="{link_zap}" target="_blank" class="zap-btn">
                🛒 Encomendar
            </a>
        </div>
        """, unsafe_allow_html=True)
