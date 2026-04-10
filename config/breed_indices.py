# config/breed_indices.py
# ─────────────────────────────────────────────────────────────────────────────
# Configuração de índices por raça.
# Para adicionar uma nova raça ou personalizar índices,
# basta adicionar um novo bloco aqui sem alterar o restante do código.
# ─────────────────────────────────────────────────────────────────────────────

BREED_INDICES = {
    "HO": {  # Holandês
        "nome_completo": "Holandês",
        "indice_principal": "TPI",
        "indices_economicos": ["NM$", "CM$", "FM$", "GM$"],
        "cor_tema": "#1565C0",  # Azul
        "icone": "🐄",
    },
    "JE": {  # Jersey
        "nome_completo": "Jersey",
        "indice_principal": "JPI",
        "indices_economicos": ["JNM$", "CM$", "FM$", "GM$"],
        "cor_tema": "#E65100",  # Laranja
        "icone": "🐄",
    },
    "GI": {  # Girolando
        "nome_completo": "Girolando",
        "indice_principal": "MÉRITOS",  # Ajustar quando disponível
        "indices_economicos": ["MÉRITOS"],
        "cor_tema": "#2E7D32",  # Verde
        "icone": "🐄",
    },
    "GIR": {  # Gir Leiteiro
        "nome_completo": "Gir Leiteiro",
        "indice_principal": "MÉRITOS",  # Ajustar quando disponível
        "indices_economicos": ["MÉRITOS"],
        "cor_tema": "#6A1B9A",  # Roxo
        "icone": "🐄",
    },
}

def get_breed_config(raca_code: str) -> dict:
    """
    Retorna configuração de índices para a raça informada.
    Se a raça não estiver mapeada, retorna configuração genérica.
    """
    return BREED_INDICES.get(raca_code.upper(), {
        "nome_completo": raca_code,
        "indice_principal": "ÍNDICE",
        "indices_economicos": [],
        "cor_tema": "#37474F",
        "icone": "🐄",
    })
