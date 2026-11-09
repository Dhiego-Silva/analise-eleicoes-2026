import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# 1. Carregar os dados consolidados das UFs
df_deputados = pd.read_csv("deputado_federal_1t.csv")

# Mapeamento dos 2 primeiros digitos para a sigla do partido
# (inclui 14 = MISSAO e 65 = PCdoB, que antes caiam em "OUTROS")
MAPA_PARTIDOS = {
    "10": "REPUBLICANOS", "11": "PP", "12": "PDT", "13": "PT", "14": "MISSAO",
    "15": "MDB", "16": "PSTU", "18": "REDE", "20": "PODEMOS", "21": "PCB",
    "22": "PL", "23": "CIDADANIA", "25": "PRD", "27": "DC", "28": "PRTB",
    "29": "PCO", "30": "NOVO", "33": "MOBILIZA", "35": "PMB", "36": "AGIR",
    "40": "PSB", "43": "PV", "44": "UNIAO", "45": "PSDB", "50": "PSOL",
    "55": "PSD", "65": "PCdoB", "70": "AVANTE", "77": "SOLIDARIEDADE", "80": "UP"
}

df_deputados["partido_numero"] = df_deputados["numero_partido"].astype(str).str.zfill(4).str[:2]
df_deputados["partido_sigla"] = df_deputados["partido_numero"].map(MAPA_PARTIDOS).fillna("OUTROS")

print("=================================================================")
print("1. PERGUNTA: Votos por candidato a deputado")
print("   METODO: Media, Mediana, Desvio Padrao e IQR")
print("=================================================================")
media = df_deputados["votos"].mean()
mediana = df_deputados["votos"].median()
std = df_deputados["votos"].std()
q1, q3 = df_deputados["votos"].quantile(0.25), df_deputados["votos"].quantile(0.75)
iqr = q3 - q1
limite_sup = q3 + 1.5 * iqr
n_outliers = (df_deputados["votos"] > limite_sup).sum()

print(f"Media:   {media:.2f}  (puxada pelos 'puxadores de voto')")
print(f"Mediana: {mediana:.2f}")
print(f"Desvio Padrao: {std:.2f}")
print(f"IQR (Q3 - Q1): {iqr:.2f}")
print(f"Limite superior de Tukey (Q3 + 1,5*IQR): {limite_sup:.2f} | candidatos acima: {n_outliers}\n")


print("=================================================================")
print("2. PERGUNTA: Partido mais votado por UF")
print("   METODO: Moda por UF (partido com mais votos em cada UF)")
print("=================================================================")
votos_partido_uf = df_deputados.groupby(["uf", "partido_sigla"])["votos"].sum().reset_index()
idx_max = votos_partido_uf.groupby("uf")["votos"].idxmax()
partido_lider_uf = votos_partido_uf.loc[idx_max].sort_values("uf")

print(partido_lider_uf.to_string(index=False))
print(f"\nModa geral (partido que lidera mais UFs): {partido_lider_uf['partido_sigla'].mode()[0]}")
print("Numero de UFs lideradas por partido:")
print(partido_lider_uf["partido_sigla"].value_counts().to_string(), "\n")


# PREPARACAO: % de votos de cada PARTIDO dentro de cada UF
# (cada deputado so aparece em uma UF; por isso a matriz por candidato seria
#  quase toda zero e sem significado. Por partido, as 27 UFs sao comparaveis.)
votos_partido_uf["total_uf"] = votos_partido_uf.groupby("uf")["votos"].transform("sum")
votos_partido_uf["pct"] = votos_partido_uf["votos"] / votos_partido_uf["total_uf"] * 100

# Matriz pivotada: linhas = uf, colunas = partido, valores = pct
X = votos_partido_uf.pivot(index="uf", columns="partido_sigla", values="pct").fillna(0)


print("=================================================================")
print("3. PERGUNTA: Partidos que andam juntos entre as UFs")
print("   METODO: Correlacao de Spearman (sobre % de votos por partido)")
print("=================================================================")
spearman_matrix = X.corr(method="spearman")
print(f"Matriz de Spearman calculada ({spearman_matrix.shape[0]}x{spearman_matrix.shape[1]}).")
pares = spearman_matrix.where(np.triu(np.ones(spearman_matrix.shape, dtype=bool), k=1)).stack()
print("\nPares mais correlacionados positivamente:")
print(pares.nlargest(5).round(2).to_string())
print("\nPares mais correlacionados negativamente:")
print(pares.nsmallest(5).round(2).to_string(), "\n")


print("=================================================================")
print("4. PERGUNTA: Perfil de votacao das UFs")
print("   METODO: Padronizacao + PCA")
print("=================================================================")
Z = StandardScaler().fit_transform(X)
pca_full = PCA().fit(Z)
acum = pca_full.explained_variance_ratio_.cumsum()

pca = PCA(n_components=2).fit(Z)
print(f"PC1: {pca.explained_variance_ratio_[0] * 100:.2f}%")
print(f"PC2: {pca.explained_variance_ratio_[1] * 100:.2f}%")
print(f"Variancia acumulada (PC1 + PC2): {acum[1] * 100:.2f}%")
n80 = int(np.argmax(acum >= 0.80)) + 1
print(f"Componentes necessarios para 80% da variancia: {n80}\n")

loadings = pd.DataFrame(pca.components_.T, index=X.columns, columns=["PC1", "PC2"])

print("=================================================================")
print("5. LEITURA DOS LOADINGS DO PCA (partidos)")
print("=================================================================")
for pc in ["PC1", "PC2"]:
    print(f"\n--- {pc} ({pca.explained_variance_ratio_[int(pc[-1]) - 1] * 100:.2f}% da variancia) ---")
    print("Maiores pesos POSITIVOS:")
    print(loadings[pc].nlargest(5).round(3).to_string())
    print("Maiores pesos NEGATIVOS:")
    print(loadings[pc].nsmallest(5).round(3).to_string())
