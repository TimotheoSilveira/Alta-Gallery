import streamlit as st
import json
import base64
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DADOS INICIAIS
# ============================================================================

INITIAL_BULLS = [
    {
        "id": 1,
        "name": "Super Bull 001",
        "code": "SB001",
        "breed": "Holandês",
        "category": "Leite",
        "description": "Excelente produção de leite e conformação.",
        "bullImage": "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80",
        "daughters": [
            {
                "id": 101,
                "cowName": "Vaca 4021",
                "farm": "Fazenda Boa Vista",
                "location": "Varginha / MG",
                "milk": "42 kg/dia",
                "lactation": "2ª lactação",
                "image": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "id": 102,
                "cowName": "Estrela 198",
                "farm": "Fazenda Santa Clara",
                "location": "Carmo do Rio Claro / MG",
                "milk": "38 kg/dia",
                "lactation": "1ª lactação",
                "image": "https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=1200&q=80"
            }
        ]
    },
    {
        "id": 2,
        "name": "Alta Prime 245",
        "code": "AP245",
        "breed": "Jersey",
        "category": "Sólidos",
        "description": "Destaque para sólidos, fertilidade e vacas funcionais.",
        "bullImage": "https://images.unsplash.com/photo-1493962853295-0fd70327578a?auto=format&fit=crop&w=900&q=80",
        "daughters": []
    },
    {
        "id": 3,
        "name": "Lineage Force 990",
        "code": "LF990",
        "breed": "Girolando",
        "category": "Tropical",
        "description": "Boa adaptação, persistência e excelente tipo leiteiro.",
        "bullImage": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80",
        "daughters": []
    }
]

# ============================================================================
# INICIALIZAR SESSION STATE - TUDO AQUI!
# ============================================================================

if "loggedIn" not in st.session_state:
    st.session_state.loggedIn = False
    st.session_state.email = ""
    st.session_state.userName = ""
    st.session_state.bulls = []
    st.session_state.users = []
    st.session_state.query = ""
    st.session_state.breedFilter = "Todas as raças"
    st.session_state.selectedBullId = None
    st.session_state.previewPhoto = None
    st.session_state.showAddBull = False
    st.session_state.showAddPhoto = False
    st.session_state.showRegister = False
    st.session_state.showEditBullPhoto = False
    st.session_state.showExport = False
    st.session_state.showImport = False
    st.session_state.mobileMenuOpen = False
    st.session_state.exportSelection = []

# ============================================================================
# FUNÇÕES DE ARMAZENAMENTO
# ============================================================================

def load_bulls():
    if Path("bulls_data.json").exists():
        with open("bulls_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return INITIAL_BULLS.copy()

def save_bulls():
    with open("bulls_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.bulls, f, indent=2, ensure_ascii=False)

def load_users():
    if Path("users_data.json").exists():
        with open("users_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_users():
    with open("users_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.users, f, indent=2, ensure_ascii=False)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_breeds():
    breeds = set(bull["breed"] for bull in st.session_state.bulls)
    return ["Todas as raças"] + sorted(list(breeds))

def get_filtered_bulls():
    filtered = []
    for bull in st.session_state.bulls:
        haystack = f"{bull['name']} {bull['code']} {bull.get('category', '')} {bull['breed']}".lower()
        matches_query = st.session_state.query.lower() in haystack
        matches_breed = (st.session_state.breedFilter == "Todas as raças" or 
                        bull["breed"] == st.session_state.breedFilter)
        if matches_query and matches_breed:
            filtered.append(bull)
    return filtered

def get_selected_bull():
    for bull in st.session_state.bulls:
        if bull["id"] == st.session_state.selectedBullId:
            return bull
    return None

# ============================================================================
# CARREGAR DADOS
# ============================================================================

if not st.session_state.bulls:
    st.session_state.bulls = load_bulls()
if not st.session_state.users:
    st.session_state.users = load_users()

# ============================================================================
# TELA DE LOGIN
# ============================================================================

if not st.session_state.loggedIn:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🐄 Alta Gallery")
        st.markdown("**Acesso liberado para e-mails com final @altagenetics.com**")
        st.divider()

        with st.form("login_form"):
            email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")

            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("Acessar", use_container_width=True)
            with col_b:
                register = st.form_submit_button("Criar cadastro", use_container_width=True)

            if submit:
                email = email.strip().lower()

                if not email.endswith("@altagenetics.com"):
                    st.error("Use um e-mail com final @altagenetics.com")
                elif not password:
                    st.error("Digite uma senha")
                else:
                    user = next((u for u in st.session_state.users if u["email"] == email), None)

                    if user and user["password"] != password:
                        st.error("Senha incorreta para este usuário cadastrado")
                    else:
                        st.session_state.loggedIn = True
                        st.session_state.email = email
                        st.session_state.userName = user["name"] if user else email.split("@")[0]
                        st.success("Bem-vindo!")
                        st.rerun()

            if register:
                st.session_state.showRegister = True
                st.rerun()

        # Modal: Registrar
        if st.session_state.showRegister:
            st.divider()
            st.markdown("### Criar cadastro")

            with st.form("register_form"):
                name = st.text_input("Nome")
                reg_email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
                reg_password = st.text_input("Senha", type="password")
                reg_confirm = st.text_input("Confirmar senha", type="password")

                if st.form_submit_button("Salvar cadastro"):
                    reg_email = reg_email.strip().lower()

                    if not name:
                        st.error("Preencha o nome")
                    elif not reg_email.endswith("@altagenetics.com"):
                        st.error("Use um e-mail com final @altagenetics.com")
                    elif not reg_password or not reg_confirm:
                        st.error("Preencha as senhas")
                    elif reg_password != reg_confirm:
                        st.error("As senhas não conferem")
                    elif any(u["email"] == reg_email for u in st.session_state.users):
                        st.error("Este e-mail já está cadastrado")
                    else:
                        new_user = {
                            "id": int(datetime.now().timestamp() * 1000),
                            "name": name,
                            "email": reg_email,
                            "password": reg_password
                        }
                        st.session_state.users.append(new_user)
                        save_users()
                        st.session_state.showRegister = False
                        st.success("Cadastro realizado! Faça login agora.")
                        st.rerun()

            if st.button("Fechar registro"):
                st.session_state.showRegister = False
                st.rerun()

# ============================================================================
# PAINEL DO USUÁRIO LOGADO
# ============================================================================

else:
    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        st.markdown("### 🐄 Alta Gallery")

    with col3:
        st.markdown(f"**{st.session_state.userName}**")
        if st.button("Sair"):
            st.session_state.loggedIn = False
            st.session_state.email = ""
            st.session_state.userName = ""
            st.rerun()

    st.divider()

    st.markdown("## Touros Cadastrados")
    st.markdown("Gerencie e visualize a progênie dos touros Alta Genetics.")

    col1, col2, col3 = st.columns(3)
    total_photos = sum(len(bull.get("daughters", [])) for bull in st.session_state.bulls)
    breeds_count = len(get_breeds()) - 1

    with col1:
        st.metric("Touros", len(st.session_state.bulls))
    with col2:
        st.metric("Raças", max(breeds_count, 0))
    with col3:
        st.metric("Fotos", total_photos)

    st.divider()

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.session_state.query = st.text_input(
            "Buscar por nome ou código do touro",
            value=st.session_state.query,
            placeholder="Digite para filtrar..."
        )

    with col2:
        st.session_state.breedFilter = st.selectbox(
            "Raça",
            get_breeds(),
            index=0
        )

    with col3:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("➕", use_container_width=True, help="Adicionar touro"):
                st.session_state.showAddBull = True
                st.rerun()
        with col_b:
            if st.button("📤", use_container_width=True, help="Exportar"):
                st.session_state.showExport = True
                st.rerun()
        with col_c:
            if st.button("📥", use_container_width=True, help="Importar"):
                st.session_state.showImport = True
                st.rerun()

    st.divider()

    # Modal: Adicionar Touro
    if st.session_state.showAddBull:
        st.markdown("### Adicionar novo touro")
        with st.form("add_bull_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nome do touro")
                code = st.text_input("Código")
            with col2:
                breed = st.selectbox("Raça", ["Holandês", "Jersey", "Girolando", "Gir Leiteiro"])
                category = st.text_input("Categoria", placeholder="Ex.: Leite, Sólidos, Tropical")

            description = st.text_area("Descrição genética", placeholder="Resumo opcional")

            col1, col2 = st.columns(2)
            with col1:
                bull_image_url = st.text_input("URL da foto do touro")
            with col2:
                bull_file = st.file_uploader("Upload da foto do touro", type=["jpg", "jpeg", "png"], key="add_bull_photo")

            if st.form_submit_button("Salvar touro"):
                if not name or not code:
                    st.error("Preencha nome e código")
                else:
                    bull_image = ""

                    if bull_file:
                        bull_image = base64.b64encode(bull_file.read()).decode()
                        bull_image = f"data:image/png;base64,{bull_image}"
                    elif bull_image_url:
                        bull_image = bull_image_url

                    new_bull = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "code": code,
                        "breed": breed,
                        "category": category,
                        "description": description,
                        "bullImage": bull_image,
                        "daughters": []
                    }
                    st.session_state.bulls.insert(0, new_bull)
                    save_bulls()
                    st.session_state.showAddBull = False
                    st.success("Touro adicionado com sucesso!")
                    st.rerun()

        if st.button("Fechar"):
            st.session_state.showAddBull = False
            st.rerun()

    # Modal: Importar
    if st.session_state.showImport:
        st.markdown("### Importar base em JSON")
        json_file = st.file_uploader("Arquivo JSON", type=["json"], key="import_file")

        if json_file:
            try:
                imported_data = json.load(json_file)
                if isinstance(imported_data, list):
                    st.session_state.bulls = imported_data
                    save_bulls()
                    st.success("Dados importados com sucesso!")
                    st.session_state.showImport = False
                    st.rerun()
                else:
                    st.error("Arquivo JSON inválido")
            except:
                st.error("Erro ao processar arquivo JSON")

        if st.button("Fechar importação"):
            st.session_state.showImport = False
            st.rerun()

    # Modal: Exportar
    if st.session_state.showExport:
        st.markdown("### Exportar touros")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Selecionar todos"):
                st.session_state.exportSelection = [b["id"] for b in st.session_state.bulls]
                st.rerun()
        with col2:
            if st.button("Limpar seleção"):
                st.session_state.exportSelection = []
                st.rerun()
        with col3:
            if st.button("Selecionar filtrados"):
                st.session_state.exportSelection = [b["id"] for b in get_filtered_bulls()]
                st.rerun()

        st.markdown(f"**{len(st.session_state.exportSelection)}** de **{len(st.session_state.bulls)}** touros selecionados")

        for bull in st.session_state.bulls:
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.checkbox("", value=bull["id"] in st.session_state.exportSelection, key=f"export_{bull['id']}"):
                    if bull["id"] not in st.session_state.exportSelection:
                        st.session_state.exportSelection.append(bull["id"])
                else:
                    if bull["id"] in st.session_state.exportSelection:
                        st.session_state.exportSelection.remove(bull["id"])

            with col2:
                st.write(f"**{bull['name']}** ({bull['code']}) - {bull['breed']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Exportar selecionados"):
                selected = [b for b in st.session_state.bulls if b["id"] in st.session_state.exportSelection]
                if selected:
                    json_data = json.dumps(selected, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="Baixar JSON",
                        data=json_data,
                        file_name="alta-gallery-selecao.json",
                        mime="application/json"
                    )
                else:
                    st.error("Selecione pelo menos um touro")

        with col2:
            if st.button("Exportar base completa"):
                json_data = json.dumps(st.session_state.bulls, indent=2, ensure_ascii=False)
                st.download_button(
                    label="Baixar JSON",
                    data=json_data,
                    file_name="alta-gallery-base-completa.json",
                    mime="application/json"
                )

        if st.button("Fechar exportação"):
            st.session_state.showExport = False
            st.rerun()

    st.divider()

    # Listagem de Touros
    filtered_bulls = get_filtered_bulls()

    if not filtered_bulls:
        st.info("Nenhum touro encontrado com esse filtro.")
    else:
        st.markdown(f"### {len(filtered_bulls)} resultado(s)")

        for bull in filtered_bulls:
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                if bull.get("bullImage"):
                    st.image(bull["bullImage"], use_column_width=True)
                else:
                    st.info("Sem foto")

            with col2:
                st.markdown(f"### {bull['name']}")
                st.markdown(f"**Código:** {bull['code']}")
                st.markdown(f"**Raça:** {bull['breed']} | **Categoria:** {bull.get('category', 'N/A')}")
                st.markdown(f"**Descrição:** {bull.get('description', 'Sem descrição')}")
                st.markdown(f"**Fotos de filhas:** {len(bull.get('daughters', []))}")

            with col3:
                if st.button("Abrir", key=f"open_{bull['id']}", use_container_width=True):
                    st.session_state.selectedBullId = bull["id"]
                    st.rerun()

                if st.button("Excluir", key=f"delete_{bull['id']}", use_container_width=True):
                    if st.checkbox(f"Confirmar exclusão", key=f"confirm_{bull['id']}"):
                        st.session_state.bulls = [b for b in st.session_state.bulls if b["id"] != bull["id"]]
                        save_bulls()
                        st.success("Touro excluído!")
                        st.rerun()

            st.divider()

    # Galeria do Touro
    selected_bull = get_selected_bull()
    if selected_bull:
        st.markdown(f"## Galeria - {selected_bull['name']} ({selected_bull['code']})")

        col1, col2 = st.columns([1, 3])
        with col1:
            if selected_bull.get("bullImage"):
                st.image(selected_bull["bullImage"], use_column_width=True)
            else:
                st.info("Sem foto")

        with col2:
            st.markdown(f"**Raça:** {selected_bull['breed']}")
            st.markdown(f"**Categoria:** {selected_bull.get('category', 'N/A')}")
            st.markdown(f"**Descrição:** {selected_bull.get('description', 'Sem descrição')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Editar foto do touro"):
                st.session_state.showEditBullPhoto = True
                st.rerun()
        with col2:
            if st.button("➕ Adicionar foto de filha"):
                st.session_state.showAddPhoto = True
                st.rerun()
        with col3:
            if st.button("Fechar galeria"):
                st.session_state.selectedBullId = None
                st.rerun()

        st.divider()

        # Modal: Editar foto do touro
        if st.session_state.showEditBullPhoto:
            st.markdown("### Editar foto do touro")
            with st.form("edit_bull_photo_form"):
                new_url = st.text_input("Nova URL da foto")
                new_file = st.file_uploader("Upload da nova foto", type=["jpg", "jpeg", "png"], key="edit_bull_photo")

                if st.form_submit_button("Salvar foto do touro"):
                    if new_file:
                        selected_bull["bullImage"] = base64.b64encode(new_file.read()).decode()
                        selected_bull["bullImage"] = f"data:image/png;base64,{selected_bull['bullImage']}"
                        save_bulls()
                        st.session_state.showEditBullPhoto = False
                        st.success("Foto atualizada!")
                        st.rerun()
                    elif new_url:
                        selected_bull["bullImage"] = new_url
                        save_bulls()
                        st.session_state.showEditBullPhoto = False
                        st.success("Foto atualizada!")
                        st.rerun()
                    else:
                        st.error("Informe uma URL ou faça upload")

            if st.button("Apagar foto do touro"):
                selected_bull["bullImage"] = ""
                save_bulls()
                st.session_state.showEditBullPhoto = False
                st.success("Foto removida!")
                st.rerun()

        # Modal: Adicionar foto de filha
        if st.session_state.showAddPhoto:
            st.markdown("### Adicionar foto de filha")
            with st.form("add_photo_form"):
                cow_name = st.text_input("Nome ou número da vaca")
                col1, col2 = st.columns(2)
                with col1:
                    farm = st.text_input("Fazenda")
                with col2:
                    location = st.text_input("Cidade / Estado")

                col1, col2 = st.columns(2)
                with col1:
                    milk = st.text_input("Produção de leite (opcional)")
                with col2:
                    lactation = st.text_input("Lactação (opcional)")

                image_url = st.text_input("URL da imagem")
                image_file = st.file_uploader("Upload da imagem", type=["jpg", "jpeg", "png"], key="add_photo_file")

                if st.form_submit_button("Salvar foto"):
                    if not cow_name:
                        st.error("Preencha o nome da vaca")
                    elif not image_url and not image_file:
                        st.error("Informe uma imagem")
                    else:
                        photo_image = ""
                        if image_file:
                            photo_image = base64.b64encode(image_file.read()).decode()
                            photo_image = f"data:image/png;base64,{photo_image}"
                        else:
                            photo_image = image_url

                        new_photo = {
                            "id": int(datetime.now().timestamp() * 1000),
                            "cowName": cow_name,
                            "farm": farm,
                            "location": location,
                            "milk": milk,
                            "lactation": lactation,
                            "image": photo_image
                        }
                        selected_bull["daughters"].insert(0, new_photo)
                        save_bulls()
                        st.session_state.showAddPhoto = False
                        st.success("Foto adicionada!")
                        st.rerun()

        # Galeria de fotos
        if selected_bull.get("daughters"):
            st.markdown(f"### Fotos de filhas ({len(selected_bull['daughters'])})")

            cols = st.columns(3)
            for idx, photo in enumerate(selected_bull["daughters"]):
                with cols[idx % 3]:
                    st.image(photo["image"], use_column_width=True)
                    st.markdown(f"**{photo['cowName']}**")
                    st.markdown(f"{photo.get('farm', '-')} | {photo.get('location', '-')}")
                    if photo.get("milk"):
                        st.markdown(f"Produção: {photo['milk']}")
                    if photo.get("lactation"):
                        st.markdown(f"Lactação: {photo['lactation']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Ampliar", key=f"preview_{photo['id']}", use_container_width=True):
                            st.session_state.previewPhoto = photo
                            st.rerun()
                    with col2:
                        if st.button("Apagar", key=f"delete_photo_{photo['id']}", use_container_width=True):
                            selected_bull["daughters"] = [p for p in selected_bull["daughters"] if p["id"] != photo["id"]]
                            save_bulls()
                            st.success("Foto removida!")
                            st.rerun()
        else:
            st.info("Nenhuma foto cadastrada para este touro ainda.")

    # Modal: Visualizar foto
    if st.session_state.previewPhoto:
        photo = st.session_state.previewPhoto
        st.markdown(f"## Visualização - {photo['cowName']}")
        st.image(photo["image"], use_column_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Vaca:** {photo['cowName']}")
        with col2:
            st.markdown(f"**Fazenda:** {photo.get('farm', '-')}")
        with col3:
            st.markdown(f"**Local:** {photo.get('location', '-')}")

        if photo.get("milk"):
            st.markdown(f"**Produção:** {photo['milk']}")
        if photo.get("lactation"):
            st.markdown(f"**Lactação:** {photo['lactation']}")

        if st.button("Fechar visualização"):
            st.session_state.previewPhoto = None
            st.rerun()
