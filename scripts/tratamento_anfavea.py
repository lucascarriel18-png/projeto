import os
import re
import sys

import pandas as pd

# Pasta com as planilhas brutas da ANFAVEA e o CSV de indicadores (Selic e IPCA)
pasta_dados = sys.argv[1] if len(sys.argv) > 1 else ('dados_brutos' if os.path.exists('dados_brutos') else '.')
arquivo_macro = sys.argv[2] if len(sys.argv) > 2 else os.path.join(pasta_dados, 'indicadores_bcb.csv')
pasta_saida = sys.argv[3] if len(sys.argv) > 3 else '.'

# 1. Indicadores econômicos (SGS/BCB: série 4189 = Selic anualizada, série 433 = IPCA mensal)
macro = pd.read_csv(arquivo_macro, sep=';', decimal=',')
macro = macro[['Ano', 'Mes', 'selic', 'ipca']].drop_duplicates(subset=['Ano', 'Mes'])
macro['selic'] = pd.to_numeric(macro['selic'], errors='coerce').round(2)
macro['ipca'] = pd.to_numeric(macro['ipca'], errors='coerce').round(2)

# 2. Regras de padronização
mapeamento_grupos = {
    'FIAT': 'Stellantis', 'JEEP': 'Stellantis', 'PEUGEOT': 'Stellantis',
    'CITROEN': 'Stellantis', 'CITROËN': 'Stellantis', 'RAM': 'Stellantis',
    'FCA': 'Stellantis', 'CHRYSLER': 'Stellantis', 'DODGE': 'Stellantis', 'LEAPMOTOR': 'Stellantis',
    'BYD': 'Chinesas', 'GWM': 'Chinesas', 'GREAT WALL': 'Chinesas',
    'CHERY': 'Chinesas', 'CHANGAN': 'Chinesas', 'JAC': 'Chinesas', 'GEELY': 'Chinesas',
    'CHEVROLET': 'General Motors', 'GENERAL MOTORS': 'General Motors',
    'VOLKSWAGEN': 'Volkswagen Group', 'AUDI': 'Volkswagen Group', 'PORSCHE': 'Volkswagen Group',
    'MAN': 'Volkswagen Group',
    'TOYOTA': 'Toyota Group', 'LEXUS': 'Toyota Group',
    'HYUNDAI': 'Hyundai Group', 'KIA': 'Hyundai Group',
    'HONDA': 'Honda', 'RENAULT': 'Renault-Nissan', 'NISSAN': 'Renault-Nissan',
    'MITSUBISHI': 'HPE', 'SUZUKI': 'HPE',
    'BMW': 'BMW Group', 'MINI': 'BMW Group',
    'MERCEDES': 'Mercedes-Benz Group',
    'VOLVO': 'Volvo Group',
    'JAGUAR': 'Jaguar Land Rover', 'LAND ROVER': 'Jaguar Land Rover',
    'OUTRAS EMPRESAS': 'Outras empresas',
}

# Nomes compostos usados pela ANFAVEA -> marca
nomes_marca = {
    'HPE (MITSUBISHI)': 'Mitsubishi', 'HPE - MITSUBISHI': 'Mitsubishi',
    'FCA (DODGE)': 'Dodge', 'FCA (FIAT/DODGE)': 'Fiat/Dodge',
    'CAOA (HYUNDAI)': 'Hyundai (Caoa)', 'CAOA - HYUNDAI': 'Hyundai (Caoa)', 'CAOA': 'Hyundai (Caoa)',
    'HYUNDAI - CAOA': 'Hyundai (Caoa)', 'HYUNDAI - CAOA CHERY': 'Caoa Chery',
    'JAGUAR LAND ROVER ( LAND ROVER)': 'Land Rover', 'JAGUAR LAND ROVER - LAND ROVER': 'Land Rover',
    'PEUGEOT CITROËN - CITROËN': 'Citroën', 'PEUGEOT CITROËN - PEUGEOT': 'Peugeot',
    'HONDA AUTOMÓVEIS': 'Honda', 'HYUNDAI': 'Hyundai (Caoa)', 'OUTRAS MARCAS': 'Outras empresas',
    'AGRALE': 'Agrale', 'IVECO': 'Iveco', 'MERCEDES-BENZ': 'Mercedes-Benz', 'SCANIA': 'Scania',
    'VOLVO': 'Volvo', 'FOTON': 'Foton',
}

# Rótulos de categorias, subtotais e totais (não são empresas)
rotulos_agregados = {
    'TOTAL', 'AUTOMÓVEIS', 'COMERCIAIS LEVES', 'CAMINHÕES', 'ÔNIBUS', 'ÔNIBUS (CHASSI)',
    'SEMILEVES', 'LEVES', 'MÉDIOS', 'SEMIPESADOS', 'PESADOS',
    'EMPRESAS ASSOCIADAS À ANFAVEA', 'EMPRESAS ASSOCIADAS A ANFAVEA',
}
BLOCO_REPETIDO = 'CAMINHÕES - TOTAL POR EMPRESA'  # repete, por empresa, os caminhões já detalhados acima
categorias_pesadas = {'CAMINHÕES', 'ÔNIBUS', 'ÔNIBUS (CHASSI)'}

contagem = {'linhas_com_rotulo': 0, 'totais_e_subtotais': 0, 'bloco_caminhoes_repetido': 0,
            'linhas_mae': 0, 'linhas_de_marca': 0}

meses_list = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def nome_marca(rotulo):
    limpo = ' '.join(rotulo.split())
    return nomes_marca.get(limpo.upper(), limpo)


def padronizar_montadora(marca):
    nome = marca.upper()
    for chave, grupo in mapeamento_grupos.items():
        if re.search(r'\b' + re.escape(chave) + r'\b', nome):
            return grupo
    return marca


def categorizar_segmento(marca, categoria):
    # 1º Pesados/Comerciais: definido pela categoria da própria planilha (caminhões e ônibus)
    if categoria in categorias_pesadas:
        return 'Pesados / Comerciais'
    nome = marca.upper()
    # 2º Eletrificados/Chinesas; 3º Premium/Luxo; demais: Volume/Tradicionais (residual)
    if any(k in nome for k in ['BYD', 'GWM', 'GREAT WALL', 'CHERY', 'CHANGAN', 'JAC', 'LEAPMOTOR', 'GEELY']):
        return 'Eletrificados / Chinesas'
    if any(k in nome for k in ['AUDI', 'BMW', 'MINI', 'MERCEDES', 'PORSCHE', 'VOLVO', 'LEXUS', 'JAGUAR', 'LAND ROVER']):
        return 'Premium / Luxo'
    return 'Volume / Tradicionais'


def ler_planilha(caminho):
    ano = int(re.search(r'20\d\d', os.path.basename(caminho)).group(0))
    xls = pd.ExcelFile(caminho)
    aba = [s for s in xls.sheet_names if 'Empresa' in s or 'NACIONAIS' in s][0]
    df = pd.read_excel(caminho, sheet_name=aba, header=None)

    linha_meses = next(i for i, r in df.iterrows() if 'Jan' in [str(x).strip() for x in r.values])
    cab = [str(x).strip() for x in df.iloc[linha_meses].values]
    col_mes = {i: meses_list.index(v) + 1 for i, v in enumerate(cab) if v in meses_list}
    primeira_col_mes = min(col_mes)

    # Cada linha vira (rótulo, profundidade, valores); profundidade = coluna do rótulo + recuo
    linhas = []
    for i in range(linha_meses + 1, len(df)):
        r = df.iloc[i]
        rot, col = None, None
        for c in range(primeira_col_mes):
            v = r.iloc[c]
            if isinstance(v, str) and v.strip():
                rot, col = v, c
        if rot is None:
            continue
        prof = col * 100 + (1 if rot.startswith(' ') else 0)  # recuo = linha filha
        valores = {m: pd.to_numeric(r.iloc[c], errors='coerce') for c, m in col_mes.items()}
        linhas.append((rot.strip(), prof, valores))

    registros, total_oficial = [], None
    categoria, pular_bloco = None, False
    contagem['linhas_com_rotulo'] += len(linhas)
    for k, (rot, prof, valores) in enumerate(linhas):
        rot_up = ' '.join(rot.split()).upper()
        if rot_up == 'TOTAL':
            total_oficial = valores
            contagem['totais_e_subtotais'] += 1
            continue
        if rot_up == BLOCO_REPETIDO:
            pular_bloco = True
            contagem['bloco_caminhoes_repetido'] += 1
            continue
        if rot_up in ('ÔNIBUS', 'ÔNIBUS (CHASSI)', 'AUTOMÓVEIS', 'COMERCIAIS LEVES', 'CAMINHÕES'):
            categoria, pular_bloco = rot_up, False
        if pular_bloco:
            contagem['bloco_caminhoes_repetido'] += 1
            continue
        if rot_up in rotulos_agregados:
            contagem['totais_e_subtotais'] += 1
            continue
        # Linha-mãe (ex.: FCA, BMW, Toyota): a linha seguinte é mais profunda -> usa só as filhas
        if k + 1 < len(linhas) and linhas[k + 1][1] > prof and \
                ' '.join(linhas[k + 1][0].split()).upper() not in rotulos_agregados:
            contagem['linhas_mae'] += 1
            continue
        contagem['linhas_de_marca'] += 1
        marca = nome_marca(rot)
        for mes, v in valores.items():
            if pd.notna(v) and v > 0:
                registros.append({'Ano': ano, 'Mes': mes, 'Marca_Montadora': marca,
                                  'Grupo_Economico': padronizar_montadora(marca),
                                  'Segmento_Mercado': categorizar_segmento(marca, categoria),
                                  'Vendas_Unidades': int(v), 'Categoria': categoria})
    return ano, aba, pd.DataFrame(registros), total_oficial


arquivos = sorted(os.path.join(pasta_dados, f) for f in os.listdir(pasta_dados) if f.endswith('.xlsx'))
partes, conferencia = [], []
for arq in arquivos:
    ano, aba, df_ano, total_oficial = ler_planilha(arq)
    partes.append(df_ano)
    soma = df_ano.groupby('Mes')['Vendas_Unidades'].sum()
    for mes, tot in total_oficial.items():
        if pd.notna(tot) and tot > 0:
            conferencia.append({'Ano': ano, 'Mes': mes, 'Total_ANFAVEA': int(tot),
                                'Total_base': int(soma.get(mes, 0))})
    print(f'{os.path.basename(arq)} (aba "{aba}"): {len(df_ano)} registros')

df = pd.concat(partes, ignore_index=True)
print('Contagem das linhas lidas:', contagem)
print('Registros marca x mês antes da consolidação:', len(df))

# 3. Consolidação: um registro por marca, segmento e mês
chaves = ['Ano', 'Mes', 'Marca_Montadora', 'Grupo_Economico', 'Segmento_Mercado']
df = df.groupby(chaves, as_index=False)['Vendas_Unidades'].sum()
df['Data'] = pd.to_datetime(df['Ano'].astype(str) + '-' + df['Mes'].astype(str).str.zfill(2) + '-01')
df = df.merge(macro, on=['Ano', 'Mes'], how='left')
df = df[['Data', 'Ano', 'Mes', 'Marca_Montadora', 'Grupo_Economico', 'Segmento_Mercado',
         'Vendas_Unidades', 'selic', 'ipca']].sort_values(['Data', 'Marca_Montadora', 'Segmento_Mercado'])

# 4. Conferência externa: soma da base x linha "Total" da própria planilha da ANFAVEA
conf = pd.DataFrame(conferencia)
conf['Diferenca'] = conf['Total_base'] - conf['Total_ANFAVEA']
print('Meses conferidos:', len(conf), '| meses com diferença:', int((conf['Diferenca'] != 0).sum()))

os.makedirs(pasta_saida, exist_ok=True)
df.to_csv(os.path.join(pasta_saida, 'dados_dw_anfavea_sem_duplicadas.csv'), index=False, sep=';', decimal=',',
          encoding='utf-8-sig', date_format='%Y-%m-%d')
df.to_excel(os.path.join(pasta_saida, 'dados_dw_anfavea_sem_duplicadas.xlsx'), index=False)
conf.to_csv(os.path.join(pasta_saida, 'conferencia_totais_anfavea.csv'), index=False, sep=';', encoding='utf-8-sig')
print('Registros finais:', len(df), '| total de unidades:', df['Vendas_Unidades'].sum())
