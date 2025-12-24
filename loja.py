import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum Store", page_icon="💎", layout="wide")

# --- ESTILO VISUAL (CSS) ---
st.markdown("""
<style>
    /* Importando APENAS a Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

    /* APLICANDO MONTSERRAT EM TUDO */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700;
    }

    /* Fundo e Cores */
    .stApp {
        background-color: #162d48; /* Azul Profundo */
        color: #FFFFFF;
    }

    /* Barra de Busca */
    .stTextInput > div > div > input {
        color: #162d48;
        background-color: #d2d2d2;
        border-radius: 25px; /* Mais arredondado */
        border: none;
        padding: 12px 20px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
    }
    
    /* Cartão do Produto */
    .product-card {
        background-color: #233e58;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 25px;
        text-align: center;
        border: 1px solid rgba(210, 210, 210, 0.1);
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        border-color: #d2d2d2;
        box-shadow: 0 12px 24px rgba(0,0,0,0.5);
    }

    /* Título do Perfume */
    .prod-title {
        font-size: 16px;
        font-weight: 600; /* Mais grosso */
        margin: 15px 0 10px 0;
        min-height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.2;
    }

    /* Preço */
    .price-tag {
        font-size: 22px;
        color: #d2d2d2;
        font-weight: 700;
        margin-bottom: 15px;
        border-top: 1px solid rgba(210,210,210, 0.1);
        padding-top: 10px;
    }

    /* Botão do WhatsApp */
    a.zap-btn {
        display: inline-block;
        width: 100%;
        padding: 14px;
        background: linear-gradient(90deg, #25D366, #128C7E);
        color: white !important;
        text-decoration: none;
        border-radius: 30px;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    a.zap-btn:hover {
        transform: scale(1.03);
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
    }
    
    /* Remove espaço extra no topo */
    .block-container {
        padding-top: 1rem;
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
        if "Produto" not in df.columns or "Preco_Venda" not in df.columns:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# --- ÁREA DA LOGO (AJUSTADA PARA FICAR MAIOR) ---
# Mudei a proporção das colunas: O meio agora é muito maior (6 partes)
c1, c2, c3 = st.columns([1, 6, 1])

with c2: 
    st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Verifica a logo e define largura maior (350px)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=350) 
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=350)
    else:
        # Texto caso não carregue a imagem
        st.markdown("<h1 style='color:#d2d2d2; font-size: 60px; font-weight:800;'>ZEIDAN</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#fff; letter-spacing: 5px; font-size: 20px;'>PARFUM</h3>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- BARRA DE BUSCA ---
c_busca1, c_busca2, c_busca3 = st.columns([1, 4, 1])
with c_busca2:
    busca = st.text_input("", placeholder="🔍 Digite o nome do perfume...")

# --- CARREGAMENTO ---
df = carregar_catalogo()

if df.empty:
    st.info("Carregando catálogo...")
    st.stop()

# --- FILTRAGEM ---
if busca:
    df = df[df["Produto"].astype(str).str.contains(busca, case=False)]

# Apenas produtos com preço
df = df[df["Preco_Venda"] != ""]

st.markdown("<br>", unsafe_allow_html=True)

# --- VITRINE ---
cols = st.columns(3)

for index, row in df.iterrows():
    with cols[index % 3]:
        # Imagem
        img_url = row.get("Imagem", "")
        if not str(img_url).startswith("http"):
            img_url = "https://cdn-icons-png.flaticon.com/512/3050/3050253.png"

        preco = str(row['Preco_Venda']).replace("R$", "").strip()
        
        # --- SEU NÚMERO ---
        TEL_ZEIDAN = "5531991668430"
        
        msg = f"Olá! Gostaria de encomendar o perfume *{row['Produto']}* (R$ {preco})."
        msg_encoded = msg.replace(" ", "%20")
        link_zap = f"https://wa.me/{TEL_ZEIDAN}?text={msg_encoded}"

        # Card
        st.markdown(f"""
        <div class="product-card">
            <div style="height: 220px; overflow: hidden; border-radius: 10px; margin-bottom: 15px; background-color: #fff;">
                <img src="{img_url}" style="width: 100%; height: 100%; object-fit: contain;">
            </div>
            <div class="prod-title">{row['Produto']}</div>
            <div class="price-tag">R$ {preco}</div>
            <a href="{link_zap}" target="_blank" class="zap-btn">
                💎 Encomendar
            </a>
        </div>
        """, unsafe_allow_html=True)
