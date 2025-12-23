import streamlit as st
import json

st.title("🕵️‍♂️ Modo Diagnóstico Zeidan")

st.write("Verificando Cofre de Segredos...")

# 1. Verifica se o cabeçalho existe
if "gcp_service_account" in st.secrets:
    st.success("✅ Cabeçalho [gcp_service_account] encontrado!")
    
    # 2. Verifica se a chave json_key existe
    if "json_key" in st.secrets["gcp_service_account"]:
        st.success("✅ Campo 'json_key' encontrado!")
        
        conteudo_bruto = st.secrets["gcp_service_account"]["json_key"]
        st.info(f"📏 Tamanho do conteúdo colado: {len(conteudo_bruto)} caracteres")
        
        # 3. Tenta ler o JSON
        try:
            creds = json.loads(conteudo_bruto)
            st.success("✅ O Python conseguiu ler o JSON! A formatação está correta.")
            
            # 4. Verifica os campos obrigatórios
            if "private_key" in creds:
                chave = creds["private_key"]
                if "-----BEGIN PRIVATE KEY-----" in chave:
                    st.success(f"✅ Chave Privada detectada! (Começa com: {chave[:30]}...)")
                else:
                    st.error("❌ A Chave Privada existe, mas parece inválida (não começa com BEGIN PRIVATE KEY).")
            else:
                st.error("❌ ERRO CRÍTICO: O campo 'private_key' SUMIU do seu arquivo.")
                
            if "client_email" in creds:
                st.success(f"✅ Email detectado: {creds['client_email']}")
            else:
                st.error("❌ ERRO: O campo 'client_email' não foi encontrado.")
                
        except json.JSONDecodeError as e:
            st.error(f"❌ ERRO DE FORMATAÇÃO: O texto colado não é um JSON válido.")
            st.error(f"Detalhe do erro: {e}")
            st.warning("Dica: Verifique se você fechou todas as chaves '}' ou se não colou texto extra.")
            
    else:
        st.error("❌ A chave 'json_key' não existe. Verifique se escreveu json_key = ''' no começo.")
else:
    st.error("❌ O cabeçalho [gcp_service_account] não existe. Verifique a primeira linha do Secrets.")
