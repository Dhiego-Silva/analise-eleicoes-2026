import base64
import json
import time
from datetime import datetime
import requests
import pandas as pd

# Lista das 27 UFs para cargos estaduais/federais
UFS_BRASIL = [
    "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma",
    "mt", "ms", "mg", "pa", "pb", "pr", "pe", "pi", "rj", "rn",
    "rs", "ro", "rr", "sc", "sp", "se", "to"
]

# Configuracao dos cargos.
# "cargos_alternativos": codigos a tentar para UFs em que o cargo muda de codigo
# (no DF nao ha deputado estadual, e sim distrital). O codigo c0008 (deputado
# distrital) foi confirmado no DevTools (aba Network) do site do TSE.
CONFIG_CARGOS = {
    "presidente": {
        "codigo_cargo": "c0001",
        "codigo_eleicao": "6257",
        "ufs": ["br"]
    },
    "governador": {
        "codigo_cargo": "c0003",
        "codigo_eleicao": "6259",
        "ufs": UFS_BRASIL
    },
    "senador": {
        "codigo_cargo": "c0005",
        "codigo_eleicao": "6259",
        "ufs": UFS_BRASIL
    },
    "deputado_federal": {
        "codigo_cargo": "c0006",
        "codigo_eleicao": "6259",
        "ufs": UFS_BRASIL
    },
    "deputado_estadual": {
        "codigo_cargo": "c0007",
        "codigo_eleicao": "6259",
        "ufs": UFS_BRASIL,
        "cargos_alternativos": {"df": ["c0008"]}
    }
}

# Prefixos alternativos de arquivo por UF: no DevTools o DF aparece como
# "df97012-c0008-e006259-u.jws" (codigo do municipio colado ao "df").
PREFIXOS_ALTERNATIVOS = {"df": ["df97012"]}

HEADERS = {
    "User-Agent": "aula-ciencia-de-dados (FAETERJ)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://resultados.tse.jus.br/"
}

FONTE = "https://resultados.tse.jus.br/oficial/ele2026/"
inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
registro = [f"Fonte: {FONTE}", f"Inicio da coleta: {inicio}"]


def extrair_candidatos(dados):
    """Busca flexivel dos candidatos no JSON do TSE."""
    candidatos = []
    if "cand" in dados:
        candidatos = dados["cand"]
    elif "carg" in dados:
        for cargo in dados["carg"]:
            if "cand" in cargo:
                candidatos.extend(cargo["cand"])
            elif "agr" in cargo:
                for agrupamento in cargo["agr"]:
                    if "cand" in agrupamento:
                        candidatos.extend(agrupamento["cand"])
                    elif "par" in agrupamento:
                        for partido in agrupamento["par"]:
                            if "cand" in partido:
                                candidatos.extend(partido["cand"])
    return candidatos


def baixar(info, uf, codigo_cargo, prefixo=None):
    prefixo = prefixo or uf
    url = (f"{FONTE}{info['codigo_eleicao']}/dados/{uf}/"
           f"{prefixo}-{codigo_cargo}-e00{info['codigo_eleicao']}-u.jws")
    resposta = requests.get(url, headers=HEADERS, timeout=30)
    if resposta.status_code != 200 or not resposta.text.strip():
        return None, resposta.status_code
    # Decodificacao URL-Safe Base64
    payload_b64 = resposta.text.split(".")[1]
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)
    dados = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
    return extrair_candidatos(dados), 200


print("==================================================")
print("       INICIANDO COLETA AUTOMATICA DE DADOS       ")
print(f"       Inicio: {inicio}")
print("==================================================")

for nome_cargo, info in CONFIG_CARGOS.items():
    print(f"\n---> Coletando cargo: {nome_cargo.upper()} ({len(info['ufs'])} UFs)...")
    lista_dfs = []
    ufs_sem_dados = []

    for uf in info["ufs"]:
        codigos = [info["codigo_cargo"]] + info.get("cargos_alternativos", {}).get(uf, [])
        candidatos, status = None, None

        prefixos = [uf] + PREFIXOS_ALTERNATIVOS.get(uf, [])

        for codigo in codigos:
            for prefixo in prefixos:
                try:
                    candidatos, status = baixar(info, uf, codigo, prefixo)
                except Exception as e:
                    status = f"erro: {e}"
                time.sleep(1)  # Pausa etica entre requisicoes
                if candidatos:
                    break
            if candidatos:
                break

        if candidatos:
            df_temp = pd.json_normalize(candidatos)
            df_temp = df_temp.rename(columns={
                "nm": "candidato",
                "vap": "votos",
                "n": "numero_partido"
            })
            df_temp["votos"] = pd.to_numeric(df_temp["votos"], errors="coerce")
            df_temp["cargo"] = nome_cargo
            df_temp["uf"] = uf.upper()
            lista_dfs.append(df_temp)
        else:
            ufs_sem_dados.append(uf.upper())
            print(f"Aviso UF {uf.upper()}: sem dados (ultimo status: {status})")

    # Salva o CSV apenas APOS percorrer todas as UFs do cargo
    if lista_dfs:
        df_completo = pd.concat(lista_dfs, ignore_index=True)
        df_completo = df_completo[["cargo", "uf", "candidato", "numero_partido", "votos"]]
        df_completo = df_completo.drop_duplicates()

        nome_csv = f"{nome_cargo}_1t.csv"
        df_completo.to_csv(nome_csv, index=False)

        total_votos = df_completo["votos"].sum()
        soma_formatada = f"{total_votos:,.0f}".replace(",", ".")
        n_ufs = df_completo["uf"].nunique()
        print(f" Arquivo '{nome_csv}' gerado com sucesso.")
        print(f"   -> Registros: {len(df_completo)} | UFs: {n_ufs} | Soma Total de Votos: {soma_formatada}")
        linha = (f"{nome_cargo}: {len(df_completo)} registros, {n_ufs} UFs, "
                 f"{soma_formatada} votos (conferir com o total do TSE)")
        if ufs_sem_dados:
            linha += f" | UFs SEM dados: {', '.join(ufs_sem_dados)}"
        registro.append(linha)

fim = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
registro.append(f"Fim da coleta: {fim}")
with open("coleta_registro.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(registro) + "\n")

print("\n==================================================")
print("       TODOS OS CARGOS FORAM COLETADOS!           ")
print("       Registro salvo em coleta_registro.txt      ")
print("==================================================")
