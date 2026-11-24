import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv('dados_dw_anfavea_sem_duplicadas.csv', sep=';', decimal=',', encoding='utf-8-sig')
conf = pd.read_csv('conferencia_totais_anfavea.csv', sep=';', encoding='utf-8-sig')

# 1) Conferência externa: total da base x linha "Total" das planilhas da ANFAVEA
print(conf.groupby('Ano')[['Total_ANFAVEA', 'Total_base', 'Diferenca']].sum())

# 2) Conferência dos visuais do painel
print('Total vendido:', df['Vendas_Unidades'].sum())
for col in ['Ano', 'Grupo_Economico', 'Marca_Montadora', 'Segmento_Mercado']:
    print(df.groupby(col)['Vendas_Unidades'].sum().sort_values(ascending=False).head(10))
seg = df.groupby('Segmento_Mercado')['Vendas_Unidades'].sum()
print((seg / seg.sum() * 100).round(2))

# 3) Médias: um valor por mês (mesma lógica das medidas com AVERAGEX)
mensal = df.groupby('Data').agg(vendas=('Vendas_Unidades', 'sum'), selic=('selic', 'first'),
                                ipca=('ipca', 'first'), Ano=('Ano', 'first'))
print('Média mensal de vendas:', mensal['vendas'].mean())
print('Selic média:', mensal['selic'].mean(), '| IPCA médio:', mensal['ipca'].mean())
print('Soma da coluna selic (erro de agregação):', df['selic'].sum())

# 4) Resumo anual (vendas, YoY, Selic média, IPCA acumulado)
anual = mensal.groupby('Ano').agg(vendas=('vendas', 'sum'), meses=('vendas', 'size'), selic=('selic', 'mean'))
anual['ipca_acum'] = mensal.groupby('Ano')['ipca'].apply(lambda s: (np.prod(1 + s / 100) - 1) * 100)
anual['yoy'] = anual['vendas'].pct_change() * 100
anual.loc[anual['meses'] < 12, 'yoy'] = np.nan  # 2026: ano parcial e só nacionais
print(anual.round(2))

# 5) Correlação mensal (2020-2025), com defasagens de 0 a 12 meses
m = mensal[mensal['Ano'] <= 2025].copy()
m['var_vendas'] = m['vendas'].pct_change(12) * 100          # variação em 12 meses (%)
m['var_selic'] = m['selic'].diff(12)                         # variação em 12 meses (p.p.)
m['ipca_12m'] = ((1 + m['ipca'] / 100).rolling(12).apply(np.prod) - 1) * 100


def corr(y, x):
    ok = x.notna() & y.notna()
    p = stats.pearsonr(y[ok], x[ok])
    s = stats.spearmanr(y[ok], x[ok])
    return int(ok.sum()), round(p[0], 2), round(p[1], 3), round(s[0], 2), round(s[1], 3)


for lag in range(13):
    print(lag,
          'nível x Selic', corr(m['vendas'], m['selic'].shift(lag)),
          'nível x IPCA', corr(m['vendas'], m['ipca'].shift(lag)),
          'var. x var. Selic', corr(m['var_vendas'], m['var_selic'].shift(lag)),
          'var. x IPCA 12m', corr(m['var_vendas'], m['ipca_12m'].shift(lag)))
