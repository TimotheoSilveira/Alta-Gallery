# gerar_hash.py
import streamlit as st
import bcrypt

st.title("🔐 Gerador de Hash de Senha")
st.caption("Use esta página para gerar o hash da senha do administrador.")

senha = st.text_input("Digite a senha:", type="password")

if st.button("Gerar Hash"):
    if senha:
        hashed = bcrypt.hashpw(
            senha.encode("utf-8"),
            bcrypt.gensalt(12)
        ).decode("utf-8")

        st.success("✅ Hash gerado com sucesso!")
        st.code(hashed, language="text")
        st.info("📋 Copie o hash acima e cole no secrets.toml no campo 'password'")
    else:
        st.warning("⚠️ Digite uma senha primeiro.")
