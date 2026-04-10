# pdf_parser.py
# Parser automático para provas de touros Holandês (formato CDCB/Alta).
# Preparado para extensão com outros formatos de raça.
import re
import pdfplumber
from io import BytesIO
from typing import Optional

def parse_proof_holstein(pdf_bytes: bytes) -> Optional[dict]:
    """
    Extrai automaticamente todos os campos da prova de um touro Holandês
    no formato CDCB/Alta Genetics.
    Retorna dicionário com todos os campos ou None em caso de falha.
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except Exception as e:
        return None

    def find(pattern: str, default: str = "") -> str:
        """Helper para extrair valor via regex."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    dados = {
        # ── Identificação ───────────────────────────────────────────────────
        "id_touro":         find(r"(\d{3}[A-Z]{2}\d+)"),
        "nome_curto":       find(r"^([A-Z][a-zA-Z]+)\n", ""),
        "nome_completo":    find(r"(PEAK [A-Z\-ET]+)"),
        "cruzamento":       find(r"([A-Z]+ X [A-Z]+ X [A-Z]+)"),
        "registro":         find(r"(HO\d+[A-Z0-9]+)\s*\|"),
        "data_nascimento":  find(r"DOB\s+(\d+/\d+/\d+)"),
        "kappa_caseina":    find(r"Kappa-Casein\s+([A-Z0-9]+)"),
        "beta_caseina":     find(r"Beta-Casein\s+([A-Z0-9]+)"),
        "haplotipos":       find(r"Haplotypes\s+([\w\s]+?)\n"),
        "codigos_geneticos":find(r"Genetic Codes\s+([\w\s]+?)\n"),
        "EFI":              find(r"EFI\s+([\d.]+)\s*%"),
        "RHA":              find(r"RHA\s+(\d+)%"),
        "prova_atual":      find(r"Current Proof\s+(\S+)"),
        "raca":             "HO",  # Parser específico para Holandês

        # ── Índices Principais ───────────────────────────────────────────────
        "TPI":   find(r"TPI\s*\n\s*([\d]+)"),
        "NM$":   find(r"NM\$\s*\n\s*([\d]+)"),
        "CM$":   find(r"CM\$\s+\$([\d]+)"),
        "FM$":   find(r"FM\$\s+\$([\d]+)"),
        "GM$":   find(r"GM\$\s+\$([\d]+)"),

        # ── Produção ────────────────────────────────────────────────────────
        "leite_lbs":      find(r"Milk\s+([+-]?\d+)\s+Lbs"),
        "leite_rel":      find(r"Milk\s+[+-]?\d+\s+Lbs\s+(\d+)%\s+Rel"),
        "proteina_lbs":   find(r"Protein\s+([+-]?\d+)\s+Lbs"),
        "proteina_pct":   find(r"Protein\s+[+-]?\d+\s+Lbs\s+([+-]?[\d.]+)%"),
        "gordura_lbs":    find(r"Fat\s+([+-]?\d+)\s+Lbs"),
        "gordura_pct":    find(r"Fat\s+[+-]?\d+\s+Lbs\s+([+-]?[\d.]+)%"),

        # ── Saúde & Eficiência ───────────────────────────────────────────────
        "vida_produtiva": find(r"Productive Life\s+([+-]?[\d.]+)"),
        "livabilidade_vaca":    find(r"Cow Livability\s+([+-]?[\d.]+)"),
        "livabilidade_novilha": find(r"Heifer Livability\s+([+-]?[\d.]+)"),
        "celulas_somaticas":    find(r"Somatic Cell Score\s+([+-]?[\d.]+)"),
        "MAST":  find(r"MAST\s+([\d.]+)%"),
        "METR":  find(r"METR\s+([\d.]+)%"),
        "DA":    find(r"DA\s+([\d.]+)%"),
        "KETO":  find(r"KETO\s+([\d.]+)%"),
        "RP":    find(r"RP\s+([\d.]+)%"),
        "MFEV":  find(r"MFEV\s+([+-]?[\d.]+)"),
        "REI":   find(r"Repro Efficiency Index\s+([+-]?[\d.]+)"),
        "FI":    find(r"Fertility Index\s+([+-]?[\d.]+)"),
        "DPR":   find(r"Daughter Pregnancy Rate\s+([+-]?[\d.]+)"),
        "CCR":   find(r"Cow Conception Rate\s+([+-]?[\d.]+)"),
        "HCR":   find(r"Heifer Conception Rate\s+([+-]?[\d.]+)"),
        "EFC":   find(r"Early First Calving\s+([+-]?[\d.]+)"),
        "DWP$":  find(r"DWP\$\s+(\d+)"),
        "WT$":   find(r"WT\$\s+(\d+)"),
        "velocidade_ordenha": find(r"Milking Speed\s+([\d.]+)"),
        "FSAV":  find(r"FSAV\s+(\d+)"),

        # ── Parto ───────────────────────────────────────────────────────────
        "ease_parto_touro_pct":  find(r"Sire Calving Ease\s+([\d.]+)%"),
        "ease_parto_touro_rel":  find(r"Sire Calving Ease\s+[\d.]+%\s+(\d+)%\s+Rel"),
        "mortinato_touro_pct":   find(r"Sire stillbirth\s+([\d.]+)%"),
        "mortinato_touro_rel":   find(r"Sire stillbirth\s+[\d.]+%\s+(\d+)%\s+Rel"),
        "ease_parto_filha_pct":  find(r"Dtr Calving Ease\s+([\d.]+)%"),
        "ease_parto_filha_rel":  find(r"Dtr Calving Ease\s+[\d.]+%\s+(\d+)%\s+Rel"),
        "mortinato_filha_pct":   find(r"Dtr stillbirth\s+([\d.]+)%"),
        "mortinato_filha_rel":   find(r"Dtr stillbirth\s+[\d.]+%\s+(\d+)%\s+Rel"),

        # ── Conformação ─────────────────────────────────────────────────────
        "PTAT":          find(r"PTAT\s+([+-]?[\d.]+)"),
        "MUI":           find(r"MUI\s+([\d.]+)"),
        "BWC":           find(r"BWC\s+([+-]?[\d.]+)"),
        "UDC":           find(r"UDC\s+([+-]?[\d.]+)"),
        "FLC":           find(r"FLC\s+([+-]?[\d.]+)"),
        "estatura":      find(r"Stature\s+([+-]?[\d.]+)"),
        "forca":         find(r"Strength\s+([+-]?[\d.]+)"),
        "prof_corporal": find(r"Body Depth\s+([+-]?[\d.]+)"),
        "forma_leiteira":find(r"Dairy form\s+([+-]?[\d.]+)"),
        "angulo_garupa": find(r"Rump Angle\s+([+-]?[\d.]+)"),
        "largura_garupa":find(r"Thurl Width\s+([+-]?[\d.]+)"),
        "pernas_lateral":find(r"R\. Legs-S View\s+([+-]?[\d.]+)"),
        "pernas_post":   find(r"R\. Legs-R View\s+([+-]?[\d.]+)"),
        "angulo_casco":  find(r"Foot Angle\s+([+-]?[\d.]+)"),
        "score_FL":      find(r"F&L Score\s+([+-]?[\d.]+)"),
        "lig_ub_ant":    find(r"F\. Udder Att\.\s+([+-]?[\d.]+)"),
        "alt_ub_post":   find(r"R\. Udder Ht\.\s+([+-]?[\d.]+)"),
        "larg_ub_post":  find(r"R\. Udder Wid\.\s+([+-]?[\d.]+)"),
        "lig_central":   find(r"Udder Cleft\s+([+-]?[\d.]+)"),
        "prof_ubere":    find(r"Udder Depth\s+([+-]?[\d.]+)"),
        "posic_tetos_ant":find(r"F\. Teat Place\s+([+-]?[\d.]+)"),
        "posic_tetos_post":find(r"R\. Teat Place\s+([+-]?[\d.]+)"),
        "comp_teto":     find(r"Teat Length\s+([+-]?[\d.]+)"),
        "conf_filhas":   find(r"CONFORMATION Based on (\d+ \w+ in \d+ \w+)"),

        # ── Pedigree ────────────────────────────────────────────────────────
        "pai":    find(r"SIRE\s+(.+)"),
        "mae":    find(r"DAM\s+(.+)"),
        "avo_mat":find(r"MGS\s+(.+)"),
        "avo_mae":find(r"MGD\s+(.+)"),
        "bisavo_mat": find(r"MGGS\s+(.+)"),
        "bisavo_mae": find(r"MGGD\s+(.+)"),
    }

    return dados


# ── Dispatcher por raça ──────────────────────────────────────────────────────
PARSERS = {
    "HO": parse_proof_holstein,
    # "JE": parse_proof_jersey,    # Adicionar quando necessário
    # "GI": parse_proof_girolando, # Adicionar quando necessário
    # "GIR": parse_proof_gir,      # Adicionar quando necessário
}

def parse_proof(pdf_bytes: bytes, raca: str) -> Optional[dict]:
    """
    Seleciona o parser correto pela raça e processa o PDF.
    """
    parser = PARSERS.get(raca.upper())
    if not parser:
        return None
    return parser(pdf_bytes)
