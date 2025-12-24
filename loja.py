import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum Store", page_icon="💎", layout="wide")

# ======================================================================
# 👇 SEU WHATSAPP AQUI
NUMERO_ZAP = "5531991668430"
# ======================================================================

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    .stApp {
        background-color: #162d48;
        color: #FFFFFF;
    }

    /* Barra de Busca - específica para o campo desta página */
    .stTextInput input[aria-label="Busca Perfume"] {
        color: #162d48;
        background-color: #d2d2d2;
        border-radius: 30px;
        border: none;
        padding: 15px 25px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        font-size: 16px;
    }
    
    /* Cartão do Produto */
    .product-card {
        background-color: #233e58;
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        border: 1px solid rgba(210, 210, 210, 0.1);
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        border-color: #d2d2d2;
        box-shadow: 0 15px 30px rgba(0,0,0,0.4);
    }

    .prod-title {
        font-size: 16px;
        font-weight: 700;
        margin: 15px 0 10px 0;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 1px;
        line-height: 1.3;
    }

    .price-tag {
        font-size: 24px;
        color: #d2d2d2;
        font-weight: 800;
        margin-bottom: 15px;
        border-top: 1px solid rgba(210,210,210, 0.1);
        padding-top: 15px;
    }

    a.zap-btn {
        display: block;
        width: 100%;
        padding: 12px;
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white !important;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    a.zap-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(37, 211, 102, 0.5);
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    try:
        if "CREDENCIAIS_JSON" in st.secrets:
            info_json = st.secrets["CREDENCIAIS_JSON"]
            creds_dict = json.loads(info_json, strict=False)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_dict, scope
            )
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
    if not sheet:
        return pd.DataFrame()
    try:
        ws = sheet.worksheet("Produtos")
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        if "Produto" not in df.columns or "Preco_Venda" not in df.columns:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# ====================== CABEÇALHO ESTILO PRINT ======================

# 1) "Menu" de marcas no topo (simulando um hambúrguer)
with st.container():
    col_menu, col_logo_placeholder = st.columns([1, 4])
    with col_menu:
        menu_marca = st.selectbox(
            "Menu",
            [
                "Todas",
                "ADYAN", "AFEER", "AFNAN", "AL HARAMAIN", "AL WATANIAH",
                "AMARAN", "ANFAR", "ANFAS", "ARD AL ZAAFARAN", "ARMAF",
                "ASTEN", "BIDAYA", "BULGARI", "BURBERRY", "CALVIN KLEIN",
                "CAROLINA HERRERA", "CHLOÉ", "COACH", "CREED", "DIOR",
                "DOLCE&GABANNA", "FERRARI", "FRENCH AVENUE",
                "GABRIELA SABATINI", "GIORGIO ARMANI", "GIVENCHY", "INITIO",
                "ISSEY MIYAKE", "JACQUES BOGART", "JEAN PAUL GAULTIER",
                "LANCÔME", "LATTAFA", "MAISON ALHAMBRA",
                "MAISON FRANCIS KURKDJIAN", "MAISON MARGIELA", "MICALLEF",
                "MEMO", "MONTALE", "MONTBLANC", "NAUTICA", "NISHANE",
                "ORIENTICA", "PACO RABBANE", "PANA DORA", "PARFUMS DE MARLY",
                "RALPH LAUREN", "ROJA PARFUMS", "SOSPIRO",
                "STÉPHANE HUMBERT LUCAS", "TOM FORD", "XERJOFF"
            ],
            index=0,
        )

# 2) Logo centralizada grande
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f'<img src="data:image/png;base64,{data}" '
        f'style="display:block;margin:auto;width:250px;max-width:80%;height:auto;padding-bottom:20px;">',
        unsafe_allow_html=True,
    )
elif os.path.exists("logo.jpg"):
    with open("logo.jpg", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f'<img src="data:image/jpeg;base64,{data}" '
        f'style="display:block;margin:auto;width:250px;max-width:80%;height:auto;padding-bottom:20px;">',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<h1 style='color:#d2d2d2; font-size: 50px; text-align: center;'>ZEIDAN PARFUM</h1>",
        unsafe_allow_html=True,
    )

# 3) Barra de busca abaixo da logo
c1, c2, c3 = st.columns([1, 4, 1])
with c2:
    busca = st.text_input(
        "Busca Perfume",
        placeholder="🔍 Digite o nome do perfume...",
        label_visibility="collapsed",
    )

# ====================== CATÁLOGO ======================

df = carregar_catalogo()

if df.empty:
    st.info("Carregando catálogo...")
    st.stop()

# Filtro por marca (se existir coluna 'Marca')
if "Marca" in df.columns and menu_marca != "Todas":
    df = df[df["Marca"] == menu_marca]

# Filtro por busca
if busca:
    df = df[df["Produto"].astype(str).str.contains(busca, case=False)]

# Remove produtos sem preço
df = df[df["Preco_Venda"] != ""]

st.markdown("<br>", unsafe_allow_html=True)

# --- LIMPEZA DO ZAP ---
zap_limpo = ''.join(filter(str.isdigit, NUMERO_ZAP))

# --- VITRINE EM 2 COLUNAS ---
cols = st.columns(2)

for index, row in df.iterrows():
    with cols[index % 2]:
        img_url = row.get("Imagem", "")
        if not str(img_url).startswith("http"):
            img_url = "https://cdn-icons-png.flaticon.com/512/3050/3050253.png"

        preco = str(row['Preco_Venda']).replace("R$", "").strip()

        msg = f"Olá! Gostaria de encomendar o perfume *{row['Produto']}* (R$ {preco})."
        msg_encoded = msg.replace(" ", "%20")
        link_zap = f"https://wa.me/{zap_limpo}?text={msg_encoded}"

        st.markdown(f"""
        <div class="product-card">
            <a href="{img_url}" target="_blank"
               style="height: 250px; display: flex; align-items: center; justify-content: center;
                      background: white; border-radius: 15px; overflow: hidden; margin-bottom: 15px;">
                <img src="{img_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </a>
            <div>
                <div class="prod-title">{row['Produto']}</div>
                <div class="price-tag">R$ {preco}</div>
                <a href="{link_zap}" target="_blank" class="zap-btn">
                    💎 Encomendar
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
