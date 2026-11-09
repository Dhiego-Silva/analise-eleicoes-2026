# Eleições 2026 (1º turno): coleta e análise estatística dos resultados do TSE

Projeto da disciplina de Análise de Negócios BigData (UVA). Coleta os resultados oficiais do 1º turno das eleições de 2026 direto da fonte do TSE e aplica métodos estatísticos para responder quatro perguntas sobre a votação.

**Autor:** [Dhiego Felisberto]

## O que o projeto faz

1. **Coleta** os resultados de 5 cargos (presidente, governador, senador, deputado federal e deputado estadual/distrital) nas 27 UFs, a partir dos arquivos JSON que o site de resultados do TSE usa.
2. **Limpa e valida** os dados com pandas (tipos numéricos, remoção de duplicatas, soma de votos por cargo).
3. **Analisa** a votação de deputado federal com quatro perguntas e métodos diferentes.
4. **Gera gráficos** por cargo e uma leitura dos resultados com seus limites.

## Perguntas e métodos

| Pergunta | Método |
|---|---|
| Quantos votos recebe um candidato típico a deputado? | Média, mediana, desvio padrão, IQR e regra de Tukey |
| Qual partido é o mais votado em cada UF? | Moda por UF (partido com mais votos) |
| Quais partidos têm desempenho parecido entre as UFs? | Correlação de Spearman sobre o % de votos por partido |
| Como as UFs se parecem no perfil de votação? | Padronização (z-score) e PCA, com leitura dos loadings |

## Principais resultados

- **Assimetria dos votos:** em deputado federal, a média é de 15.232,97 votos por candidato e a mediana é de 1.207,50. O desvio padrão (66.521,91) é muito maior que a média, e 1.233 candidaturas ficam acima do limite de Tukey (14.814,25). Por isso o resumo adequado é a mediana com o IQR (5.788,50).
- **Partido líder por UF:** o PL lidera em 13 das 27 UFs, seguido por MDB (4), REPUBLICANOS (3) e PT (2). PP, UNIÃO, PSB, NOVO e PSD lideram uma UF cada.
- **PCA:** PC1 explica 16,76% e PC2, 11,34% da variância (28,09% juntas). São necessários 10 componentes para chegar a 80%, então o gráfico em 2D é um resumo parcial.

## Decisão metodológica importante

A análise multivariada usa o **% de votos de cada partido em cada UF**, e não os candidatos como variáveis. Cada deputado concorre em uma única UF, então uma matriz UF × candidato seria quase toda zero (cerca de 96%), e a correlação e o PCA não teriam significado.

## Estrutura

```
.
├── 01_coleta.py                 # coleta e gera os CSVs
├── 02_analise.py                # análise em linha de comando
├── analise_eleicoes_2026.ipynb  # notebook com análise e gráficos
├── coleta_registro.txt          # fonte, horário e totais da coleta
├── presidente_1t.csv
├── governador_1t.csv
├── senador_1t.csv
├── deputado_federal_1t.csv
└── deputado_estadual_1t.csv     # no DF, são deputados distritais
```

Colunas dos CSVs: `cargo`, `uf`, `candidato`, `numero_partido`, `votos`.

## Como rodar

Requisitos: Python 3 com `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests` e `jupyter`.

```bash
pip install pandas numpy scikit-learn matplotlib seaborn requests jupyter
```

- **Só a análise (com os CSVs já incluídos):** abra o notebook e execute todas as células, exceto a 1, ou rode `python 02_analise.py`.
- **Refazer a coleta:** rode `python 01_coleta.py`. Leva alguns minutos por causa da pausa de 1 segundo entre requisições e sobrescreve os CSVs. Os resultados podem mudar se o TSE atualizar os dados.

## Fonte e validação

- **Fonte:** https://resultados.tse.jus.br/oficial/ele2026/ (coleta de 09/11/2026, 18:01 a 18:04, conforme `coleta_registro.txt`).
- **Boas práticas:** User-Agent identificado e pausa de 1 segundo entre chamadas.
- **Validação:** para presidente, os votos coletados diferem em 235 (Flávio Bolsonaro) e 2.921 (Lula) dos valores divulgados no portal do TSE, cerca de 0,003% do total de votos válidos (119.300.788). Os demais cargos não foram conferidos com o TSE.

## Limites e cuidados

- Os dados são agregados estaduais do 1º turno. Não é possível inferir a motivação individual do eleitor (falácia ecológica) nem causalidade.
- O DF entra em deputado estadual com os deputados distritais, cargo equivalente.
- No Senado, cada eleitor tem dois votos. Por isso os gráficos usam votos absolutos, e não percentuais calculados sobre o total.
- Com apenas 27 UFs, as correlações de Spearman são exploratórias.
- Os resultados refletem a coleta indicada acima; resultados oficiais podem ser atualizados pelo TSE.