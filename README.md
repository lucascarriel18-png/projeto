# Análise de dados de vendas de veículos no Brasil

Painel interativo em Power BI com dados de emplacamento da ANFAVEA (janeiro de 2020 a fevereiro de 2026) e indicadores econômicos do Banco Central (Selic e IPCA).

Trabalho de Conclusão de Curso – Engenharia de Software, UNICESUMAR.
Autor: Lucas Rafael Carriel de Lima.

## Conteúdo

| Pasta | Arquivos |
|---|---|
| `dados_brutos/` | Planilhas originais da ANFAVEA (2020 a 2026). A de 2026 traz apenas veículos nacionais. |
| `dados/` | `indicadores_bcb.csv` (SGS: série 4189 – Selic; série 433 – IPCA), base tratada `dados_dw_anfavea_sem_duplicadas` (CSV e Excel) e `conferencia_totais_anfavea.csv` (base × linha "Total" da ANFAVEA). |
| `scripts/` | `tratamento_anfavea.py` (tratamento das planilhas) e `validacao.py` (conferência dos indicadores e correlação). |
| `painel/` | Arquivo do painel em Power BI. |

## Como executar

```
python scripts/tratamento_anfavea.py dados_brutos dados/indicadores_bcb.csv dados
cd dados && python ../scripts/validacao.py
```

Requer Python 3 com pandas, openpyxl, numpy e scipy.

## Base tratada

3.161 registros (marca × segmento × mês), 14.199.889 unidades. Os totais mensais coincidem com a linha "Total" das planilhas da ANFAVEA em 72 dos 74 meses (diferença de 9 unidades em 2020, presente na própria planilha).
