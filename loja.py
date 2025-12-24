import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum Store", page_icon="💎", layout="wide")

# --- ESTILO VISUAL (CSS) ---
# Aqui acontece a mágica do design
st.markdown("""
<style>
    /* Importando Fontes Elegantes do Google */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Montserrat:wght@300;400;600&display=swap');

    /* 1. Fundo e Fontes Gerais */
    .stApp {
        background-color: #162d48; /* Azul Profundo (Fundo) */
        color: #FFFFFF;
        font-family: 'Montserrat', sans-serif;
    }

    /* 2. Títulos (H1, H2, H3) com fonte Serifada (Estilo Dior/Vogue) */
    h1, h2, h3, .prod-title {
        font-family: 'Playfair Display', serif !important;
    }

    /* 3. Ajuste da Barra de Busca */
    .stTextInput > div > div > input {
        color: #162d48;
        background-color: #d2d2d2; /* Prata */
        border-radius: 20px;
        border: none;
        padding: 10px 15px;
    }
    
    /* 4. Cartão do Produto */
    .product-card {
        background-color: #233e58; /* Azul Médio */
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        border: 1px solid rgba(210, 210, 210, 0.2); /* Borda prateada sutil */
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Efeito ao passar o mouse no card */
    .product-card:hover {
        transform: translateY(-5px); /* Sobe um pouquinho */
        border-color: #d2d2d2; /* Borda fica mais forte */
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }

    /* Título do Perfume */
    .prod-title {
        font-size: 18px;
        font-weight: 400;
        margin: 15px 0 5px 0;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Preço */
    .price-tag {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        color: #d2d2d2; /* Prata */
        font-weight: 300;
        margin-bottom: 15px;
        border-top: 1px solid rgba(210,210,210, 0.2);
        padding-top: 10px;
    }

    /* Botão do WhatsApp */
    a.zap-btn {
        display: inline-block;
        width: 100%;
        padding: 12px;
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important;
        text-decoration: none;
        border-radius: 25px; /* Botão redondinho */
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.5px;
        transition: transform 0.2s;
        text-transform: uppercase;
    }
    a.zap-btn:hover {
        transform: scale(1.05);
        opacity: 0.9;
    }
    
    /* Remover margens extras do topo */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO (LÓGICA BLINDADA) ---
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
        # Verifica se as colunas existem
        if "Produto" not in df.columns or "Preco_Venda" not in df.columns:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# --- ÁREA DA LOGO E TÍTULO ---
c1, c2, c3 = st.columns([1, 2, 1])

with c2: # Coluna do meio (Centralizada)
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    
    # Tenta carregar a logo (png ou jpg)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200) # Logo maior
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=200)
    else:
        # Se não tiver logo, mostra texto bonito
        st.markdown("<h1 style='color:#d2d2d2; font-size: 50px;'>ZEIDAN</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#fff; letter-spacing: 4px; font-size: 18px;'>PARFUM</h3>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- BARRA DE BUSCA ---
c_busca1, c_busca2, c_busca3 = st.columns([1, 2, 1])
with c_busca2:
    busca = st.text_input("", placeholder="🔍 Qual perfume você deseja hoje?")

# --- CARREGAMENTO ---
df = carregar_catalogo()

if df.empty:
    st.info("Carregando as melhores fragrâncias...")
    st.stop()

# --- FILTRAGEM ---
if busca:
    df = df[df["Produto"].astype(str).str.contains(busca, case=False)]

# Remove produtos sem preço
df = df[df["Preco_Venda"] != ""]

st.markdown("<br>", unsafe_allow_html=True)

# --- VITRINE (GRID) ---
# Usamos container do Streamlit para ajustar responsividade
cols = st.columns(3) # 3 colunas no desktop

for index, row in df.iterrows():
    with cols[index % 3]:
        # Imagem
        img_url = row.get("Imagem", "")
        if not str(img_url).startswith("http"):
            # Ícone elegante se não tiver foto
            img_url = "https://cdn-icons-png.flaticon.com/512/3050/3050253.png" 

        preco = str(row['Preco_Venda']).replace("R$", "").strip()
        
        # --- SEU NÚMERO AQUI ---
        TEL_ZEIDAN = "5531991668430" "5531971789632"
        
        msg = f"Olá! Gostaria de encomendar o perfume *{row['Produto']}* (R$ {preco})."
        msg_encoded = msg.replace(" ", "%20")
        link_zap = f"https://wa.me/{TEL_ZEIDAN}?text={msg_encoded}"

        # HTML do Card
        st.markdown(f"""
        <div class="product-card">
            <div style="height: 200px; overflow: hidden; border-radius: 8px; margin-bottom: 10px;">
                <img src="{img_url}" style="width: 100%; height: 100%; object-fit: contain;">
            </div>
            <div class="prod-title">{row['Produto']}</div>
            <div class="price-tag">R$ {preco}</div>
            <a href="{link_zap}" target="_blank" class="zap-btn">
                💎 Encomendar
            </a>
        </div>
        """, unsafe_allow_html=True)
