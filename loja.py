import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# --- CONFIG DA PÁGINA ---
st.set_page_config(page_title="Zeidan Parfum - Catálogo", page_icon="💎", layout="wide")

# --- ESTILO (CSS PARA FICAR BONITO) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #25D366; /* Cor do WhatsApp */
        color: white;
        border: none;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #128C7E;
        color: white;
    }
    .card-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .price-tag {
        font-size: 22px;
        color: #d4af37; /* Dourado */
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM A PLANILHA (Mesma lógica do sistema) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "CREDENCIAIS_JSON" in st.secrets:
            info_json = st.secrets["CREDENCIAIS_JSON"]
            creds_dict = json.loads(info_json, strict=False)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("Controle Zeidan Parfum") # Abre pelo nome
        else:
            return None
    except:
        return None

# --- CARREGAR PRODUTOS ---
@st.cache_data(ttl=60) # Atualiza a cada 60 segundos
def carregar_catalogo():
    sheet = conectar_google_sheets()
    if not sheet: return pd.DataFrame()
    
    try:
        ws = sheet.worksheet("Produtos")
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        return df
    except:
        return pd.DataFrame()

# --- HEADER DO SITE ---
st.title("💎 Zeidan Parfum")
st.markdown("### Seleção exclusiva de perfumes importados")
st.markdown("---")

df = carregar_catalogo()

if df.empty:
    st.info("Carregando catálogo...")
    st.stop()

# --- FILTRO DE BUSCA ---
busca = st.text_input("🔍 Buscar perfume...", placeholder="Digite o nome do perfume (ex: Dior, Lattafa...)")
if busca:
    df = df[df["Produto"].str.contains(busca, case=False)]

# --- EXIBIÇÃO EM GRADE (GRID) ---
# Vamos mostrar 3 ou 4 produtos por linha
cols = st.columns(3) # Mude para 2 se quiser maior no celular

for index, row in df.iterrows():
    # Usa a coluna da vez (0, 1 ou 2)
    with cols[index % 3]: 
        st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center;">
            <div class="card-title">{row['Produto']}</div>
            <div class="price-tag">R$ {row['Preco_Venda']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Se tiver imagem na planilha, mostra. Se não, mostra nada.
        if "Imagem" in row and str(row["Imagem"]).startswith("http"):
            st.image(row["Imagem"], use_container_width=True)
        else:
            # Imagem genérica se não tiver foto
            st.image("https://cdn-icons-png.flaticon.com/512/3050/3050253.png", width=100)

        # Botão do WhatsApp
        texto_msg = f"Olá! Vi o perfume *{row['Produto']}* no site por R$ {row['Preco_Venda']} e tenho interesse."
        texto_encoded = texto_msg.replace(" ", "%20")
        numero_whatsapp = "5531999999999" # TROQUE PELO SEU NÚMERO (COM DDD)
        link_zap = f"https://wa.me/{numero_whatsapp}?text={texto_encoded}"
        
        st.link_button("📲 Encomendar no WhatsApp", link_zap)
        st.markdown("---")
