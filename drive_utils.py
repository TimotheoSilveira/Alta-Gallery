@st.cache_data(ttl=300)
def load_progenies(id_touro: str) -> pd.DataFrame:
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            f"/gviz/tq?tqx=out:csv&sheet=progenies"
        )
        df = pd.read_csv(url)
        df = df.dropna(how="all").reset_index(drop=True)

        if df.empty or "id_touro_pai" not in df.columns:
            return pd.DataFrame()

        return df[
            df["id_touro_pai"].astype(str) == str(id_touro)
        ].reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Erro ao carregar filhas: {e}")
        return pd.DataFrame()
