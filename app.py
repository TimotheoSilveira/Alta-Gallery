import streamlit as st
import json
from datetime import datetime
from PIL import Image
import io
from google_drive_manager import GoogleDriveManager

# Configuração da página
st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    :root {
        --blue: #0b57b7;
        --blue-dark: #0a3f8f;
        --bg: #f5f7fb;
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--bg);
    }

    .bull-card {
        border: 1px solid #dbe3ee;
        border-radius: 20px;
        padding: 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(13, 63, 138, 0.08);
    }

    .stat-card {
        background: white;
        border: 1px solid #dbe3ee;
        border-radius: 18px;
        padding: 16px;
        text-align: center;
    }

    .badge {
        background: linear-gradient(135deg, #21a4ff, #0b57b7);
        color: white;
        padding: 6px 12px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Inicializa gerenciador do Google Drive
@st.cache_resource
def get_drive_manager():
    return GoogleDriveManager()

drive_manager = get_drive_manager()

# Inicializa estado da sessão
if 'bulls' not in st.session_state:
    st.session_state.bulls = drive_manager.load_bulls_data()

if 'loggedIn' not in st.session_state:
    st.session_state.loggedIn = False

if 'email' not in st.session_state:
    st.session_state.email = ""

# Página de Login
def render_login():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image("https://via.placeholder.com/150?text=Alta+Genetics", width=100)
        st.title("Alta Gallery")
        st.markdown("### Acesso liberado para @altagenetics.com")

        with st.form("login_form"):
            email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Acessar", use_container_width=True)

            if submit:
                if not email.endswith("@altagenetics.com"):
                    st.error("Use um e-mail com final @altagenetics.com")
                elif not password:
                    st.error("Informe uma senha")
                else:
                    st.session_state.loggedIn = True
                    st.session_state.email = email
                    st.rerun()

# Página do Dashboard
def render_dashboard():
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("🐄 Alta Gallery")
        st.markdown("Gerencie e visualize a progênie dos touros Alta Genetics")

    with col3:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.loggedIn = False
            st.session_state.email = ""
            st.rerun()

    st.divider()

    # Estatísticas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Touros Cadastrados", len(st.session_state.bulls))

    with col2:
        breeds = set(bull.get('breed', '') for bull in st.session_state.bulls)
        st.metric("Raças", len(breeds))

    with col3:
        total_photos = sum(len(bull.get('daughters', [])) for bull in st.session_state.bulls)
        st.metric("Fotos de Filhas", total_photos)

    st.divider()

    # Filtros
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input("🔎 Buscar por nome ou código do touro...")

    with col2:
        breeds_list = ["Todas as raças"] + sorted(set(bull.get('breed', '') for bull in st.session_state.bulls))
        breed_filter = st.selectbox("Raça", breeds_list)

    st.divider()

    # Ações
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ Adicionar Touro", use_container_width=True):
            st.session_state.show_add_bull = True

    with col2:
        if st.button("📥 Importar", use_container_width=True):
            st.session_state.show_import = True

    with col3:
        if st.button("📤 Exportar", use_container_width=True):
            st.session_state.show_export = True

    with col4:
        if st.button("🔄 Resetar", use_container_width=True):
            if st.session_state.get('confirm_reset'):
                st.session_state.bulls = []
                drive_manager.save_bulls_data([])
                st.session_state.confirm_reset = False
                st.success("Dados resetados!")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("Clique novamente para confirmar")

    st.divider()

    # Filtrar touros
    filtered_bulls = st.session_state.bulls

    if search_query:
        filtered_bulls = [
            bull for bull in filtered_bulls
            if search_query.lower() in f"{bull['name']} {bull['code']}".lower()
        ]

    if breed_filter != "Todas as raças":
        filtered_bulls = [bull for bull in filtered_bulls if bull.get('breed') == breed_filter]

    # Exibir cards dos touros
    if filtered_bulls:
        for bull in filtered_bulls:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if bull.get('bullImage'):
                        st.image(bull['bullImage'], width=150)
                    else:
                        st.info("Sem foto")

                with col2:
                    st.subheader(bull['name'])
                    st.markdown(f"**Código:** {bull['code']}")
                    st.markdown(f"<span class='badge'>{bull.get('breed', 'N/A')}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Categoria:** {bull.get('category', '-')}")
                    st.markdown(f"{bull.get('description', 'Sem descrição')}")
                    st.markdown(f"**{len(bull.get('daughters', []))} fotos de filhas**")

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if st.button("📸 Abrir Galeria", key=f"open_{bull['id']}"):
                            st.session_state.selected_bull_id = bull['id']
                            st.session_state.show_bull_modal = True

                    with col_b:
                        if st.button("✏️ Editar", key=f"edit_{bull['id']}"):
                            st.session_state.selected_bull_id = bull['id']
                            st.session_state.show_edit_bull = True

                    with col_c:
                        if st.button("🗑️ Excluir", key=f"delete_{bull['id']}"):
                            st.session_state.bulls = [b for b in st.session_state.bulls if b['id'] != bull['id']]
                            drive_manager.save_bulls_data(st.session_state.bulls)
                            st.success("Touro excluído!")
                            st.rerun()
    else:
        st.info("Nenhum touro encontrado com esse filtro.")

    # Modal: Adicionar Touro
    if st.session_state.get('show_add_bull'):
        st.divider()
        st.subheader("➕ Adicionar Novo Touro")

        with st.form("add_bull_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Nome do touro")
                code = st.text_input("Código")
                breed = st.selectbox("Raça", ["Holandês", "Jersey", "Girolando", "Gir Leiteiro"])

            with col2:
                category = st.text_input("Categoria (ex: Leite, Sólidos)")
                description = st.text_area("Descrição genética")

            bull_image_url = st.text_input("URL da foto do touro")
            bull_image_file = st.file_uploader("Ou faça upload da foto", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("Salvar Touro", use_container_width=True):
                if not name or not code:
                    st.error("Preencha nome e código")
                else:
                    bull_image = None

                    if bull_image_file:
                        image_bytes = bull_image_file.read()
                        bull_image = drive_manager.upload_image(image_bytes, f"bull_{code}_{datetime.now().timestamp()}.jpg")
                    elif bull_image_url:
                        bull_image = bull_image_url

                    new_bull = {
                        'id': int(datetime.now().timestamp() * 1000),
                        'name': name,
                        'code': code,
                        'breed': breed,
                        'category': category,
                        'description': description,
                        'bullImage': bull_image,
                        'daughters': []
                    }

                    st.session_state.bulls.append(new_bull)
                    drive_manager.save_bulls_data(st.session_state.bulls)
                    st.session_state.show_add_bull = False
                    st.success("Touro adicionado com sucesso!")
                    st.rerun()

def render_daughter_gallery(bull):
    st.subheader(f"📸 Galeria — {bull['name']} ({bull['code']})")

    # Upload de nova foto de filha
    with st.expander("➕ Adicionar foto de filha"):
        uploaded = st.file_uploader(
            "Selecione uma imagem", type=["jpg", "jpeg", "png"],
            key=f"daughter_upload_{bull['id']}"
        )
        caption = st.text_input("Legenda (opcional)", key=f"caption_{bull['id']}")

        if st.button("Enviar foto", key=f"send_{bull['id']}"):
            if uploaded:
                image_bytes = uploaded.read()
                filename = f"{bull['code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                url = drive_manager.upload_daughter_image(
                    image_bytes, filename, bull['code']
                )
                daughter_entry = {"url": url, "caption": caption, "filename": filename}
                bull['daughters'].append(daughter_entry)

                # Atualiza o touro na lista principal
                for i, b in enumerate(st.session_state.bulls):
                    if b['id'] == bull['id']:
                        st.session_state.bulls[i] = bull
                        break

                drive_manager.save_bulls_data(st.session_state.bulls)
                st.success("Foto enviada!")
                st.rerun()
            else:
                st.warning("Selecione uma imagem primeiro.")

    # Exibição das fotos em grade
    daughters = drive_manager.list_daughter_images(bull['code'])

    if daughters:
        cols = st.columns(3)
        for idx, daughter in enumerate(daughters):
            with cols[idx % 3]:
                st.image(daughter['url'], use_container_width=True)
                st.caption(daughter['name'])
    else:
        st.info("Nenhuma foto de filha cadastrada ainda.")

    if st.button("← Voltar", key="back_gallery"):
        st.session_state.show_bull_modal = False
        st.rerun()

# Renderizar página apropriada
if not st.session_state.loggedIn:
    render_login()
else:
    render_dashboard()

# Modal: Galeria de filhas
if st.session_state.get('show_bull_modal') and st.session_state.get('selected_bull_id'):
    bull = next(
        (b for b in st.session_state.bulls if b['id'] == st.session_state.selected_bull_id),
        None
    )
    if bull:
        st.divider()
        render_daughter_gallery(bull)
