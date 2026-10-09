

**Este bloco de código em Python realiza a etapa inicial de extração (E) do processo de ETL (Extração, Transformação e Carga) dos relatórios brutos da ANFAVEA.**





import pandas as pd

import glob

import re

import os

from google.colab import files



pasta\_dados = 'dados\_brutos' if os.path.exists('dados\_brutos') else '.'



\# 1. Carregar indicadores econômicos com Selic corrigida

macro\_files = \[os.path.join(pasta\_dados, f) for f in os.listdir(pasta\_dados) if 'dados\_analiticos\_finais' in f]

if not macro\_files:

&#x20;   macro\_files = \[f for f in os.listdir('.') if 'dados\_analiticos\_finais' in f]



if macro\_files:

&#x20;   df\_macro = pd.read\_csv(macro\_files\[0], sep=';')

&#x20;   macro\_indicators = df\_macro\[\['Ano', 'Mes', 'selic', 'ipca']].drop\_duplicates()

&#x20;   # Garante que a Selic esteja formatada como número decimal simples (arredondado em 2 casas)

&#x20;   macro\_indicators\['selic'] = pd.to\_numeric(macro\_indicators\['selic'], errors='coerce').round(2)

&#x20;   macro\_indicators\['ipca'] = pd.to\_numeric(macro\_indicators\['ipca'], errors='coerce').round(2)

else:

&#x20;   macro\_indicators = pd.DataFrame(columns=\['Ano', 'Mes', 'selic', 'ipca'])



\# 2. Regras de Padronização e Mapeamentos

mapeamento\_grupos = {

&#x20;   'FIAT': 'Stellantis', 'JEEP': 'Stellantis', 'PEUGEOT': 'Stellantis', 

&#x20;   'CITROEN': 'Stellantis', 'CITROËN': 'Stellantis', 'RAM': 'Stellantis', 

&#x20;   'BYD': 'Chinesas', 'GWM': 'Chinesas', 'GREAT WALL': 'Chinesas', 

&#x20;   'CHERY': 'Chinesas', 'CAOA CHERY': 'Chinesas', 'JAC': 'Chinesas',

&#x20;   'CHEVROLET': 'General Motors', 'GM': 'General Motors', 'GENERAL MOTORS': 'General Motors',

&#x20;   'VOLKSWAGEN': 'Volkswagen Group', 'VW': 'Volkswagen Group', 'AUDI': 'Volkswagen Group',

&#x20;   'TOYOTA': 'Toyota Group', 'LEXUS': 'Toyota Group',

&#x20;   'HYUNDAI': 'Hyundai Group', 'KIA': 'Hyundai Group',

&#x20;   'HONDA': 'Honda', 'RENAULT': 'Renault-Nissan', 'NISSAN': 'Renault-Nissan',

&#x20;   'BMW': 'BMW Group'

}



def padronizar\_montadora(nome):

&#x20;   if pd.isna(nome): return 'Outras'

&#x20;   nome\_limpo = str(nome).strip().upper()

&#x20;   for chave, grupo in mapeamento\_grupos.items():

&#x20;       if chave in nome\_limpo:

&#x20;           return grupo

&#x20;   return str(nome).strip().title()



def categorizar\_segmento(empresa):

&#x20;   emp\_upper = str(empresa).upper()

&#x20;   if any(k in emp\_upper for k in \['BYD', 'GWM', 'CHERY', 'JAC']):

&#x20;       return 'Eletrificados / Chinesas'

&#x20;   elif any(k in emp\_upper for k in \['AUDI', 'BMW', 'MERCEDES', 'PORSCHE', 'VOLVO', 'LEXUS']):

&#x20;       return 'Premium / Luxo'

&#x20;   elif any(k in emp\_upper for k in \['SCANIA', 'VOLVO CAMINHÕES', 'MAN', 'IVECO', 'MERCEDES-BENZ CAMINHÕES']):

&#x20;       return 'Pesados / Comerciais'

&#x20;   return 'Volume / Tradicionais'



meses\_list = \['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

registros = \[]



\# Lista de termos/totalizadores para IGNORAR (evita duplicar totais)

ignorar\_marcas = \[

&#x20;   'TOTAL', 'AUTOMÓVEIS', 'COMERCIAIS LEVES', 'CAMINHÕES', 'ÔNIBUS', 'UNIDADES',

&#x20;   'EMPRESAS ASSOCIADAS À ANFAVEA', 'EMPRESAS ASSOCIADAS A ANFAVEA'

]



excel\_files = sorted(\[os.path.join(pasta\_dados, f) for f in os.listdir(pasta\_dados) if f.endswith('.xlsx')])



for f in excel\_files:

&#x20;   match\_ano = re.search(r'202\\d', f)

&#x20;   if not match\_ano: 

&#x20;       continue

&#x20;   ano\_arq = int(match\_ano.group(0))

&#x20;   

&#x20;   try:

&#x20;       xls = pd.ExcelFile(f)

&#x20;       aba\_list = \[s for s in xls.sheet\_names if 'Empresa' in s or 'NACIONAIS' in s or 'Empresas' in s]

&#x20;       if not aba\_list: 

&#x20;           aba\_list = xls.sheet\_names

&#x20;           

&#x20;       df\_raw = pd.read\_excel(f, sheet\_name=aba\_list\[0])

&#x20;       linha\_meses = None

&#x20;       

&#x20;       for idx, row in df\_raw.iterrows():

&#x20;           if 'Jan' in \[str(x).strip() for x in row.values]:

&#x20;               linha\_meses = idx

&#x20;               break

&#x20;               

&#x20;       if linha\_meses is not None:

&#x20;           header = \[str(x).strip() for x in df\_raw.iloc\[linha\_meses].values]

&#x20;           month\_cols = {i: meses\_list.index(v) + 1 for i, v in enumerate(header) if v in meses\_list}

&#x20;           

&#x20;           for idx in range(linha\_meses + 1, len(df\_raw)):

&#x20;               row = df\_raw.iloc\[idx]

&#x20;               empresa = None

&#x20;               for c in range(0, 5):

&#x20;                   v = str(row.iloc\[c]).strip()

&#x20;                   if v and v.lower() != 'nan' and not v.replace('.', '', 1).replace(',', '', 1).isdigit():

&#x20;                       empresa = v

&#x20;               

&#x20;               # Filtra apenas marcas reais

&#x20;               if empresa and empresa.strip().upper() not in ignorar\_marcas:

&#x20;                   for col\_i, mes\_num in month\_cols.items():

&#x20;                       try:

&#x20;                           v\_num = float(str(row.iloc\[col\_i]).replace(',', '.'))

&#x20;                           if pd.notna(v\_num) and v\_num > 0:

&#x20;                               registros.append({

&#x20;                                   'Ano': ano\_arq,

&#x20;                                   'Mes': mes\_num,

&#x20;                                   'Marca\_Montadora': empresa,

&#x20;                                   'Grupo\_Economico': padronizar\_montadora(empresa),

&#x20;                                   'Segmento\_Mercado': categorizar\_segmento(empresa),

&#x20;                                   'Vendas\_Unidades': int(v\_num)

&#x20;                               })

&#x20;                       except: pass

&#x20;   except Exception as e:

&#x20;       print(f"Erro ao ler {f}: {e}")



\# 3. Exportação e Limpeza Final

if registros:

&#x20;   df\_final = pd.DataFrame(registros)

&#x20;   df\_final\['Data'] = pd.to\_datetime(df\_final\['Ano'].astype(str) + '-' + df\_final\['Mes'].astype(str).str.zfill(2) + '-01')

&#x20;   

&#x20;   df\_final = pd.merge(df\_final, macro\_indicators, on=\['Ano', 'Mes'], how='left')

&#x20;   

&#x20;   colunas = \['Data', 'Ano', 'Mes', 'Marca\_Montadora', 'Grupo\_Economico', 'Segmento\_Mercado', 'Vendas\_Unidades', 'selic', 'ipca']

&#x20;   df\_final = df\_final\[\[c for c in colunas if c in df\_final.columns]]

&#x20;   

&#x20;   # Salva com vírgula como separador decimal para abrir perfeitamente no Excel brasileiro

&#x20;   df\_final.to\_csv('dados\_dw\_anfavea\_corrigido.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

&#x20;   print("Base corrigida gerada com sucesso!")

&#x20;   files.download('dados\_dw\_anfavea\_corrigido.csv')







**Código Definitivo (Versão Final sem Subtotais)**



import pandas as pd

import glob

import re

import os

from google.colab import files



pasta\_dados = 'dados\_brutos' if os.path.exists('dados\_brutos') else '.'



\# 1. Carregar indicadores econômicos

macro\_files = \[os.path.join(pasta\_dados, f) for f in os.listdir(pasta\_dados) if 'dados\_analiticos\_finais' in f]

if not macro\_files:

&#x20;   macro\_files = \[f for f in os.listdir('.') if 'dados\_analiticos\_finais' in f]



if macro\_files:

&#x20;   df\_macro = pd.read\_csv(macro\_files\[0], sep=';')

&#x20;   macro\_indicators = df\_macro\[\['Ano', 'Mes', 'selic', 'ipca']].drop\_duplicates()

&#x20;   macro\_indicators\['selic'] = pd.to\_numeric(macro\_indicators\['selic'], errors='coerce').round(2)

&#x20;   macro\_indicators\['ipca'] = pd.to\_numeric(macro\_indicators\['ipca'], errors='coerce').round(2)

else:

&#x20;   macro\_indicators = pd.DataFrame(columns=\['Ano', 'Mes', 'selic', 'ipca'])



\# 2. Regras de Padronização Completa de Fusões e Grupos

mapeamento\_grupos = {

&#x20;   'FIAT': 'Stellantis', 'JEEP': 'Stellantis', 'PEUGEOT': 'Stellantis', 

&#x20;   'CITROEN': 'Stellantis', 'CITROËN': 'Stellantis', 'RAM': 'Stellantis', 

&#x20;   'FCA': 'Stellantis', 'CHRYSLER': 'Stellantis', 'DODGE': 'Stellantis',

&#x20;   'BYD': 'Chinesas', 'GWM': 'Chinesas', 'GREAT WALL': 'Chinesas', 

&#x20;   'CHERY': 'Chinesas', 'CAOA CHERY': 'Chinesas', 'JAC': 'Chinesas', 'LEAPMOTOR': 'Chinesas', 'GEELY': 'Chinesas',

&#x20;   'CHEVROLET': 'General Motors', 'GM': 'General Motors', 'GENERAL MOTORS': 'General Motors',

&#x20;   'VOLKSWAGEN': 'Volkswagen Group', 'VW': 'Volkswagen Group', 'AUDI': 'Volkswagen Group', 'PORSCHE': 'Volkswagen Group',

&#x20;   'TOYOTA': 'Toyota Group', 'LEXUS': 'Toyota Group',

&#x20;   'HYUNDAI': 'Hyundai Group', 'KIA': 'Hyundai Group',

&#x20;   'HONDA': 'Honda', 'RENAULT': 'Renault-Nissan', 'NISSAN': 'Renault-Nissan',

&#x20;   'BMW': 'BMW Group', 'MINI': 'BMW Group',

&#x20;   'MERCEDES': 'Mercedes-Benz Group',

&#x20;   'VOLVO': 'Volvo Group'

}



def padronizar\_montadora(nome):

&#x20;   if pd.isna(nome): return 'Outras'

&#x20;   nome\_limpo = str(nome).strip().upper()

&#x20;   for chave, grupo in mapeamento\_grupos.items():

&#x20;       if chave in nome\_limpo:

&#x20;           return grupo

&#x20;   return str(nome).strip().title()



def categorizar\_segmento(empresa):

&#x20;   emp\_upper = str(empresa).upper()

&#x20;   if any(k in emp\_upper for k in \['BYD', 'GWM', 'CHERY', 'JAC', 'LEAPMOTOR', 'GEELY']):

&#x20;       return 'Eletrificados / Chinesas'

&#x20;   elif any(k in emp\_upper for k in \['AUDI', 'BMW', 'MINI', 'MERCEDES', 'PORSCHE', 'VOLVO', 'LEXUS', 'JAGUAR', 'LAND ROVER']):

&#x20;       return 'Premium / Luxo'

&#x20;   elif any(k in emp\_upper for k in \['SCANIA', 'MAN', 'IVECO', 'DAF', 'AGRALE', 'FOTON', 'CAMINHÕES']):

&#x20;       return 'Pesados / Comerciais'

&#x20;   return 'Volume / Tradicionais'



meses\_list = \['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

registros = \[]



\# Lista de rótulos de subtotais e categorias para descartar

ignorar\_marcas = \[

&#x20;   'TOTAL', 'AUTOMÓVEIS', 'COMERCIAIS LEVES', 'CAMINHÕES', 'ÔNIBUS', 'UNIDADES',

&#x20;   'EMPRESAS ASSOCIADAS À ANFAVEA', 'EMPRESAS ASSOCIADAS A ANFAVEA',

&#x20;   'CAMINHÕES - TOTAL POR EMPRESA', 'SEMILEVES', 'LEVES', 'MÉDIOS', 'SEMIPESADOS', 'PESADOS', 'ÔNIBUS (CHASSI)'

]



excel\_files = sorted(\[os.path.join(pasta\_dados, f) for f in os.listdir(pasta\_dados) if f.endswith('.xlsx')])



for f in excel\_files:

&#x20;   match\_ano = re.search(r'202\\d', f)

&#x20;   if not match\_ano: 

&#x20;       continue

&#x20;   ano\_arq = int(match\_ano.group(0))

&#x20;   

&#x20;   try:

&#x20;       xls = pd.ExcelFile(f)

&#x20;       aba\_list = \[s for s in xls.sheet\_names if 'Empresa' in s or 'NACIONAIS' in s or 'Empresas' in s]

&#x20;       if not aba\_list: 

&#x20;           aba\_list = xls.sheet\_names

&#x20;           

&#x20;       df\_raw = pd.read\_excel(f, sheet\_name=aba\_list\[0])

&#x20;       linha\_meses = None

&#x20;       

&#x20;       for idx, row in df\_raw.iterrows():

&#x20;           if 'Jan' in \[str(x).strip() for x in row.values]:

&#x20;               linha\_meses = idx

&#x20;               break

&#x20;               

&#x20;       if linha\_meses is not None:

&#x20;           header = \[str(x).strip() for x in df\_raw.iloc\[linha\_meses].values]

&#x20;           month\_cols = {i: meses\_list.index(v) + 1 for i, v in enumerate(header) if v in meses\_list}

&#x20;           

&#x20;           for idx in range(linha\_meses + 1, len(df\_raw)):

&#x20;               row = df\_raw.iloc\[idx]

&#x20;               empresa = None

&#x20;               for c in range(0, 5):

&#x20;                   v = str(row.iloc\[c]).strip()

&#x20;                   if v and v.lower() != 'nan' and not v.replace('.', '', 1).replace(',', '', 1).isdigit():

&#x20;                       empresa = v

&#x20;               

&#x20;               if empresa and empresa.strip().upper() not in ignorar\_marcas:

&#x20;                   for col\_i, mes\_num in month\_cols.items():

&#x20;                       try:

&#x20;                           v\_num = float(str(row.iloc\[col\_i]).replace(',', '.'))

&#x20;                           if pd.notna(v\_num) and v\_num > 0:

&#x20;                               registros.append({

&#x20;                                   'Ano': ano\_arq,

&#x20;                                   'Mes': mes\_num,

&#x20;                                   'Marca\_Montadora': empresa,

&#x20;                                   'Grupo\_Economico': padronizar\_montadora(empresa),

&#x20;                                   'Segmento\_Mercado': categorizar\_segmento(empresa),

&#x20;                                   'Vendas\_Unidades': int(v\_num)

&#x20;                               })

&#x20;                       except: pass

&#x20;   except Exception as e:

&#x20;       print(f"Erro ao ler {f}: {e}")



\# 3. Exportação do Arquivo Final

df\_final = pd.DataFrame(registros)

df\_final\['Data'] = pd.to\_datetime(df\_final\['Ano'].astype(str) + '-' + df\_final\['Mes'].astype(str).str.zfill(2) + '-01')

df\_final = pd.merge(df\_final, macro\_indicators, on=\['Ano', 'Mes'], how='left')



colunas = \['Data', 'Ano', 'Mes', 'Marca\_Montadora', 'Grupo\_Economico', 'Segmento\_Mercado', 'Vendas\_Unidades', 'selic', 'ipca']

df\_final = df\_final\[colunas]



df\_final.to\_csv('dados\_dw\_anfavea\_perfeito.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

print("Base final limpa gerada com sucesso!")

files.download('dados\_dw\_anfavea\_perfeito.csv')













**Código em Python para somar as duplicadas e formatar os decimais:**

import pandas as pd

from google.colab import files



\# 1. Carrega o arquivo garantindo o separador ponto e vírgula (;) e decimal vírgula (,)

df = pd.read\_csv('dados\_dw\_anfavea\_corrigido.csv', sep=';', decimal=',')



print(f"Linhas lidas do arquivo bruto: {len(df)}")



\# 2. Agrupa e soma as vendas duplicadas no mesmo Ano/Mês de forma 100% segura

df\_final = df.groupby(

&#x20;   \['Data', 'Ano', 'Mes', 'Marca\_Montadora', 'Grupo\_Economico', 'Segmento\_Mercado', 'selic', 'ipca'],

&#x20;   as\_index=False

)\['Vendas\_Unidades'].sum()



print(f"Linhas finais consolidadas (sem duplicadas): {len(df\_final)}")



\# 3. Salva a base perfeitamente limpa nos formatos finais (.xlsx e .csv)

df\_final.to\_excel('dados\_dw\_anfavea\_sem\_duplicadas.xlsx', index=False)

df\_final.to\_csv('dados\_dw\_anfavea\_sem\_duplicadas.csv', index=False, sep=',', decimal='.', encoding='utf-8-sig')



print("Sucesso absoluto! Arquivos limpos prontos para o GitHub.")



\# 4. Dispara o download automático

files.download('dados\_dw\_anfavea\_sem\_duplicadas.xlsx')

files.download('dados\_dw\_anfavea\_sem\_duplicadas.csv')

