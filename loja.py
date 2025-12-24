import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum Store", page_icon="💎", layout="wide")

# ==============================================================================
# 👇 SEU WHATSAPP AQUI
NUMERO_ZAP = "5531991668430" 
# ==============================================================================

# --- ESTILO VISUAL (CSS MONTSERRAT + CORREÇÃO DA LOGO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    /* Fundo */
    .stApp {
        background-color: #162d48;
        color: #FFFFFF;
    }

    /* Barra de Busca */
    .stTextInput > div > div > input {
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

    /* Título do Perfume */
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

    /* Preço */
    .price-tag {
        font-size: 24px;
        color: #d2d2d2;
        font-weight: 800;
        margin-bottom: 15px;
        border-top: 1px solid rgba(210,210,210, 0.1);
        padding-top: 15px;
    }

    /* Botão do WhatsApp */
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
    
    /* Espaçamento do container principal */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* --- CORREÇÃO DA LOGO --- */
    /* Isso força a imagem a ser um bloco centralizado com tamanho fixo */
    .logo-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 250px; /* Tamanho fixo ideal */
        max-width: 80%; /* Segurança pra celular muito pequeno */
        height: auto;
        padding-bottom: 20px;
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

# --- ÁREA DA LOGO (HTML DIRETO) ---
# Removemos colunas do Streamlit para usar CSS puro na logo
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f'<img src="data:image/png;base64,{data}" class="logo-img">', unsafe_allow_html=True)

elif os.path.exists("logo.jpg"):
    with open("logo.jpg", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f'<img src="data:image/jpeg;base64,{data}" class="logo-img">', unsafe_allow_html=True)

else:
    st.markdown("<h1 style='color:#d2d2d2; font-size: 50px; text-align: center;'>ZEIDAN PARFUM</h1>", unsafe_allow_html=True)


# --- BARRA DE BUSCA ---
c1, c2, c3 = st.columns([1, 4, 1])
with c2:
    busca = st.text_input("", placeholder="🔍 Digite o nome do perfume...")

# --- CARREGAMENTO ---
df = carregar_catalogo()

if df.empty:
    st.info("Carregando catálogo...")
    st.stop()

if busca:
    df = df[df["Produto"].astype(str).str.contains(busca, case=False)]

df = df[df["Preco_Venda"] != ""]

st.markdown("<br>", unsafe_allow_html=True)

# --- LIMPEZA DO ZAP ---
zap_limpo = ''.join(filter(str.isdigit, NUMERO_ZAP))

# --- VITRINE ---
cols = st.columns(3)

for index, row in df.iterrows():
    with cols[index % 3]:
        # Imagem
        img_url = row.get("Imagem", "")
        # Se estiver vazio ou não for link, usa genérico
        if not str(img_url).startswith("http"):
            img_url = "https://cdn-icons-png.flaticon.com/512/3050/3050253.png"

        preco = str(row['Preco_Venda']).replace("R$", "").strip()
        
        # Link Zap
        msg = f"Olá! Gostaria de encomendar o perfume *{row['Produto']}* (R$ {preco})."
        msg_encoded = msg.replace(" ", "%20")
        link_zap = f"https://wa.me/{zap_limpo}?text={msg_encoded}"

        # Card HTML (Fundo Branco na área da imagem para destacar frasco)
        st.markdown(f"""
        <div class="product-card">
            <div style="height: 250px; display: flex; align-items: center; justify-content: center; background: white; border-radius: 15px; overflow: hidden; margin-bottom: 15px;">
                <img src="{img_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </div>
            <div>
                <div class="prod-title">{row['Produto']}</div>
                <div class="price-tag">R$ {preco}</div>
                <a href="{link_zap}" target="_blank" class="zap-btn">
                    💎 Encomendar
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
