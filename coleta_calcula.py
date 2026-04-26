import pandas as pd
import requests
import zipfile
import io
import os
import gc
import time
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import sqlite3

def coleta_dados_despesas():
    for ano in range(2014, datetime.now().year + 1):
        for mes in range(1, 13):

            if os.path.exists(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"):
                print(f"Dados de {ano}-{mes:02d} já existem localmente. Pulando download...")
                continue

            # Adicionamos um 'User-Agent' para evitar que o portal bloqueie a requisição automática
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            url = f"https://portaldatransparencia.gov.br/download-de-dados/despesas-execucao/{ano}{mes:02d}"

            sucesso = False

            while not sucesso:
                try:
                    print(f"Baixando os dados de {ano}-{mes:02d}...", end=' ', flush=True)

                    response = requests.get(url, headers=headers)

                    if response.status_code == 200:
                        # Abre o conteúdo binário como um arquivo ZIP
                        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                            # Lista os arquivos dentro do zip para você saber o nome exato
                            lista_arquivos = z.namelist()
                            
                            # Lê o primeiro CSV da lista (único arquivo presente)
                            nome_arquivo = lista_arquivos[0]
                            
                            with z.open(nome_arquivo) as f:
                                df = pd.read_csv(
                                    f,
                                    encoding='latin1',
                                    sep=';',
                                    decimal=',',
                                    usecols=['Ano e mês do lançamento', 'Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'],
                                    low_memory=False
                                )

                                
                        # Criar pasta para salvar os dados, se não existir
                        os.makedirs("dados", exist_ok=True)
                        os.makedirs(f"dados/dados_{ano}", exist_ok=True)
                        
                        # Salvar localmente
                        df.to_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", index=False, encoding='utf-8')

                        # 2. Divide a coluna 'Ano e mês de lançamento' em duas novas: 'ano' e 'mes'
                        df[['Ano', 'Mes']] = df['Ano e mês do lançamento'].str.split('/', expand=True)

                        df['Numero_Identificador'] = ((df['Valor Empenhado (R$)'].astype(float) + df['Valor Liquidado (R$)'].astype(float) + df['Valor Pago (R$)'].astype(float))*100).astype(int)

                        # 3. (Opcional) Converter para inteiros, já que no banco usamos INT
                        df['Ano'] = df['Ano'].astype(int)
                        df['Mes'] = df['Mes'].astype(int)

                        # 4. Agora você pode remover a coluna original se não for mais usar
                        df = df.drop(columns=['Ano e mês do lançamento'])

                        os.makedirs("dados_json", exist_ok=True)
                        os.makedirs(f"dados_json/dados_{ano}_json", exist_ok=True)
                        df.to_json(f"dados_json/dados_{ano}_json/dados_{ano}{mes:02d}.json", orient='records')
                            
                        print("Sucesso!")
                        sucesso = True

                        # LIMPEZA DE MEMÓRIA
                        del df
                        gc.collect()
                    else:
                        print(f"Erro ao baixar: Status {response.status_code}")
                        return
                except Exception as e:
                    print(f"\nFalha na conexão: {e}.")

def atualiza_dados_despesas():
    # Adicionamos um 'User-Agent' para evitar que o portal bloqueie a requisição automática
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    url = f"https://portaldatransparencia.gov.br/download-de-dados/despesas-execucao/{datetime.now().year}{datetime.now().month:02d}"

    sucesso = False

    while not sucesso:
        try:
            print(f"Baixando os dados de {datetime.now().year}-{datetime.now().month:02d}...", end=' ', flush=True)

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                # Abre o conteúdo binário como um arquivo ZIP
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # Lista os arquivos dentro do zip para você saber o nome exato
                    lista_arquivos = z.namelist()
                    
                    # Lê o primeiro CSV da lista (único arquivo presente)
                    nome_arquivo = lista_arquivos[0]
                    
                    with z.open(nome_arquivo) as f:
                        df = pd.read_csv(
                            f,
                            encoding='latin1',
                            sep=';',
                            decimal=',',
                            usecols=['Ano e mês do lançamento', 'Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'],
                            low_memory=False
                        )

                # 2. Divide a coluna 'Ano e mês de lançamento' em duas novas: 'ano' e 'mes'
                df[['Ano', 'Mes']] = df['Ano e mês do lançamento'].str.split('/', expand=True)

                df['Numero_Identificador'] = ((df['Valor Empenhado (R$)'].astype(float) + df['Valor Liquidado (R$)'].astype(float) + df['Valor Pago (R$)'].astype(float))*100).astype(int)

                # 3. (Opcional) Converter para inteiros, já que no banco usamos INT
                df['Ano'] = df['Ano'].astype(int)
                df['Mes'] = df['Mes'].astype(int)

                # 4. Agora você pode remover a coluna original se não for mais usar
                df = df.drop(columns=['Ano e mês do lançamento'])

                os.makedirs("dados_json", exist_ok=True)
                os.makedirs(f"dados_json/dados_{datetime.now().year}_json", exist_ok=True)
                df.to_json(f"dados_json/dados_{datetime.now().year}_json/dados_{datetime.now().year}{datetime.now().month:02d}.json", orient='records')
                    
                print("Sucesso!")
                sucesso = True

                # LIMPEZA DE MEMÓRIA
                del df
                gc.collect()
            else:
                print(f"Erro ao baixar: Status {response.status_code}")
                return
        except Exception as e:
            print(f"\nFalha na conexão: {e}.")

def salva_dados_json(dados, nome_arquivo):
    dados.to_json(nome_arquivo, orient="records", indent=4, force_ascii=False)
    return nome_arquivo

def salva_dados_sql(dados, nome_arquivo):
    conn = sqlite3.connect(nome_arquivo)
    dados.to_sql("despesas", conn, if_exists="replace", index=False)
    conn.close()

def soma_despesas_ano(ano, despesa):
    for mes in range(1, 13):
        if not os.path.exists(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"):
            continue
        df = pd.read_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", encoding='utf-8', decimal=',', thousands='.', usecols=[despesa], low_memory=False)
        total_despesas_mes = df[despesa].sum()
        total_despesas_ano = total_despesas_mes if mes == 1 else total_despesas_ano + total_despesas_mes
        del df
        gc.collect()
    return total_despesas_ano

def media_despesas_ano(ano, despesa):
    meses_somados = 0
    for mes in range(1, 13):
        media_despesas = 0
        if not os.path.exists(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"):
            continue
        df = pd.read_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", encoding='utf-8', decimal=',', thousands='.', usecols=[despesa], low_memory=False)
        total_despesas_mes = df[despesa].sum()
        #print(total_despesas_mes)
        meses_somados += 1
        media_despesas += total_despesas_mes
        del df
        gc.collect()
    media_despesas = media_despesas / meses_somados if meses_somados > 0 else 0
    return media_despesas

def gera_dfs(ano_inicio, ano_fim, funcao):
    resultados = []
    for ano in range(ano_inicio, ano_fim + 1):
        print(f"Calculando para o ano de {ano}... ", end=' ', flush=True)
        resultados.append({
            'Ano': ano,
            'Valor Empenhado': funcao(ano, 'Valor Empenhado (R$)'),
            'Valor Liquidado': funcao(ano, 'Valor Liquidado (R$)'),
            'Valor Pago': funcao(ano, 'Valor Pago (R$)')
        })
        print("Concluído!")
        
    return pd.DataFrame(resultados)

def gera_dfs_por_orgao(ano):
    dfs_meses = []

    for mes in range(1, 13):
        caminho = f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"

        if not os.path.exists(caminho):
            continue

        df = pd.read_csv(caminho, encoding='utf-8', decimal=',', thousands='.', usecols=['Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'],low_memory=False)

        resumo_mes = df.groupby('Nome Órgão Superior').sum().reset_index()
        dfs_meses.append(resumo_mes)

        del df
        gc.collect()
    
    if not dfs_meses:
        return pd.DataFrame()  # Retorna um DataFrame vazio se nenhum dado foi encontrado
    
    df_ano = pd.concat(dfs_meses).groupby('Nome Órgão Superior').sum().reset_index()
    return df_ano

        


def gera_grafico_barras(entrada, eixo_x, categoria, valor, titulo = "Gŕafico em Colunas"):

    if isinstance(entrada, str):
        df = pd.read_json(entrada)
    elif isinstance(entrada, pd.DataFrame):
        df = entrada
    else:
        raise ValueError("Entrada deve ser um caminho para JSON ou um DataFrame")

    #Derretendo o DataFrame para facilitar a plotagem
    df_melted = df.melt(id_vars=eixo_x, var_name=categoria, value_name=valor)

    # Gráfico de barras comparando gastos por ano
    sns.barplot(data=df_melted, x=eixo_x, y=valor, hue=categoria, palette='viridis')

    plt.title(titulo, fontsize=16)
    plt.xlabel(eixo_x, fontsize=12)
    if df_melted[valor].max() > 1e15:
        plt.ylabel("Valor (Quadrilhões R$)", fontsize=12)
    elif df_melted[valor].max() > 1e12:
        plt.ylabel("Valor (Trilhões R$)", fontsize=12)    
    elif df_melted[valor].max() > 1e9:
        plt.ylabel("Valor (Bilhões R$)", fontsize=12)
    elif df_melted[valor].max() > 1e6:
        plt.ylabel("Valor (Milhões R$)", fontsize=12)
    else:
        plt.ylabel("Valor (R$)", fontsize=12)
    plt.show()

def gera_grafico_curvas_suaves(df, coluna_x, coluna_y, titulo):
    """
    Gera um gráfico de linhas com curvas suavizadas (Spline).
    """
    # Criamos o gráfico de linha normal
    fig = px.line(df, x=coluna_x, y=coluna_y, title=titulo)
    
    # A mágica acontece aqui: alteramos o 'shape' da linha para 'spline'
    fig.update_traces(line_shape='spline', line_smoothing=1.3)
    
    # Melhorando o visual (opcional)
    fig.update_layout(
        xaxis_title=coluna_x.replace('_', ' ').title(),
        yaxis_title='Valor (R$)',
        legend_title='Etapas da Despesa',
        template='plotly_white'
    )
    
    fig.show()

def gera_grafico_pizza(df, valores, nomes, titulo):
    """
    Gera um gráfico de pizza interativo.
    df: DataFrame com os dados
    valores: Coluna numérica (ex: 'valor_pago')
    nomes: Coluna de categorias (ex: 'orgao_superior')
    titulo: Título do gráfico
    """
    fig = px.pie(
        df, 
        values=valores, 
        names=nomes, 
        title=titulo,
        hole=0.3 # Isso transforma a pizza em uma 'Rosca' (Donut), que é mais moderna
    )
    
    # Melhora a exibição das etiquetas (mostra nome e porcentagem)
    fig.update_traces(textinfo='percent+label')
    
    fig.show()

def gera_grafico_barras_horizontal(entrada, eixo_y, categoria, valor, titulo = "Gŕafico em Colunas"):

    if isinstance(entrada, str):
        df = pd.read_json(entrada)
    elif isinstance(entrada, pd.DataFrame):
        df = entrada
    else:
        raise ValueError("Entrada deve ser um caminho para JSON ou um DataFrame")

    df_melted = df.melt(id_vars=eixo_y, var_name=categoria, value_name=valor)

    sns.barplot(data=df_melted, y=eixo_y, x=valor, hue=categoria, palette='viridis')
    plt.ylabel(eixo_y, fontsize=12)
    if df_melted[valor].max() > 1e15:
        plt.xlabel("Valor (Quadrilhões R$)", fontsize=12)
    elif df_melted[valor].max() > 1e12:
        plt.xlabel("Valor (Trilhões R$)", fontsize=12)    
    elif df_melted[valor].max() > 1e9:
        plt.xlabel("Valor (Bilhões R$)", fontsize=12)
    elif df_melted[valor].max() > 1e6:
        plt.xlabel("Valor (Milhões R$)", fontsize=12)
    else:
        plt.xlabel("Valor (R$)", fontsize=12)

    plt.title(titulo, fontsize=16)
    plt.show()

def apaga_CSVs():
    for ano in range(2014, datetime.now().year + 1):
        for mes in range(1, 13):
            caminho = f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"
            if os.path.exists(caminho):
                os.remove(caminho)
                print(f"Arquivo {caminho} removido.")
            else:
                print(f"Arquivo {caminho} não encontrado.")

def reseta_dados():

    inicio = time.time()

    print("Coleta dos dados...")
    coleta_dados_despesas()
    
    print(f"Tempo de execução da coleta: {time.time() - inicio:.2f} segundos")

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto total a cada ano...")
    df = gera_dfs(2014, datetime.now().year, soma_despesas_ano)
    salva_dados_json(df, "dados_despesas_anuais.json")


    print(f"Tempo de processamento da evolução das despesas públicas: {time.time() - inicio:.2f} segundos")    

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto médio mensal a cada ano...")
    df = gera_dfs(2014, datetime.now().year, media_despesas_ano)
    salva_dados_json(df, "dados_despesas_medias_anuais.json")
    print(f"Tempo de cálculo da média mensal das despesas públicas: {time.time() - inicio:.2f} segundos")

    os.makedirs("gastos_por_orgao_json", exist_ok=True)

    for ano in range(2014, datetime.now().year + 1):
        inicio = time.time()
        print(f"\nCalculando o gasto por orgão para o ano de {ano}...")
        df = gera_dfs_por_orgao(ano)

        salva_dados_json(df, f"gastos_por_orgao_json/gasto_por_orgao_{ano}.json")

        print(f"Tempo total de execução: {time.time() - inicio:.2f} segundos")

def atualiza_dados():

    print("Coleta dos dados...")
    atualiza_dados_despesas()

    df = pd.read_json("dados_despesas_anuais.json")
    df_ano_atual = gera_dfs(datetime.now().year, datetime.now().year, soma_despesas_ano)

    df.loc[df['Ano'] == datetime.now().year, ['Valor Empenhado', 'Valor Liquidado', 'Valor Pago']] = df_ano_atual[['Valor Empenhado', 'Valor Liquidado', 'Valor Pago']].values

    salva_dados_json(df, "dados_despesas_anuais.json")

    df = pd.read_json("dados_despesas_medias_anuais.json")
    df_ano_atual = gera_dfs(datetime.now().year, datetime.now().year, media_despesas_ano)

    df.loc[df['Ano'] == datetime.now().year, ['Valor Empenhado', 'Valor Liquidado', 'Valor Pago']] = df_ano_atual[['Valor Empenhado', 'Valor Liquidado', 'Valor Pago']].values

    salva_dados_json(df, "dados_despesas_medias_anuais.json")

    os.makedirs("gastos_por_orgao_json", exist_ok=True)

    print(f"Calculando o gasto por orgão para o ano de {datetime.now().year}...")
    df = gera_dfs_por_orgao(datetime.now().year)

    salva_dados_json(df, f"gastos_por_orgao_json/gasto_por_orgao_{datetime.now().year}.json")

def main():

    inicio = time.time()

    print("Coleta dos dados...")
    coleta_dados_despesas()
    
    print(f"Tempo de execução da coleta: {time.time() - inicio:.2f} segundos")

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto total a cada ano...")
    df = gera_dfs(2014, datetime.now().year, soma_despesas_ano)
    json_path = salva_dados_json(df, "dados_despesas_anuais.json")
    #salva_dados_sql(df, "dados_despesas_anuais.db")

    print(f"Maior valor empenhado:{df["Valor Empenhado"].max()} em {df.loc[df["Valor Empenhado"].idxmax(), "Ano"]}")
    print(f"Maior valor liquidado:{df["Valor Liquidado"].max()} em {df.loc[df["Valor Liquidado"].idxmax(), "Ano"]}")
    print(f"Maior valor pago:{df["Valor Pago"].max()} em {df.loc[df["Valor Pago"].idxmax(), "Ano"]}")
    print()
    print(f"Menor valor empenhado:{df["Valor Empenhado"].min()} em {df.loc[df["Valor Empenhado"].idxmin(), "Ano"]}")
    print(f"Menor valor liquidado:{df["Valor Liquidado"].min()} em {df.loc[df["Valor Liquidado"].idxmin(), "Ano"]}")
    print(f"Menor valor pago:{df["Valor Pago"].min()} em {df.loc[df["Valor Pago"].idxmin(), "Ano"]}")


    print(f"Tempo de processamento da evolução das despesas públicas: {time.time() - inicio:.2f} segundos")

    #gera_grafico_barras(json_path, 'Ano', 'Etapa de Despesa', 'Valor (R$)', f'Evolução Anual das Despesas Públicas ({df["Ano"].min()}-{df["Ano"].max()})')

    

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto médio mensal a cada ano...")
    df = gera_dfs(2014, datetime.now().year, media_despesas_ano)
    json_path = salva_dados_json(df, "dados_despesas_medias_anuais.json")
    #salva_dados_sql(df, "dados_despesas_medias_anuais.db")
    print(f"Tempo de cálculo da média mensal das despesas públicas: {time.time() - inicio:.2f} segundos")
    #gera_grafico_barras(json_path, 'Ano', 'Etapa de Despesa', 'Valor (R$)', f'Média Mensal das Despesas Públicas ({df["Ano"].min()}-{df["Ano"].max()})')

    os.makedirs("gastos_por_orgao_json", exist_ok=True)
    #os.makedirs("gastos_por_orgao_db", exist_ok=True)

    for ano in range(2014, datetime.now().year + 1):
        inicio = time.time()
        print(f"\nCalculando o gasto por orgão para o ano de {ano}...")
        df = gera_dfs_por_orgao(ano)#.nlargest(10, 'Valor Pago (R$)')

        json_path = salva_dados_json(df, f"gastos_por_orgao_json/gasto_por_orgao_{ano}.json")
        #salva_dados_sql(df, f"gastos_por_orgao_db/gasto_por_orgao_{ano}.db")

        print(f"Tempo total de execução: {time.time() - inicio:.2f} segundos")
        #gera_grafico_barras_horizontal(json_path, 'Nome Órgão Superior', 'Etapa de Despesa', 'Valor (R$)', f'Top 10 Órgãos com Maior Valor Pago em {ano}')

def testes ():

    colunas = ['Ano e mês do lançamento', 'Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)']

    for ano in range(2014, datetime.now().year + 1):
        for mes in range(1, 13):
            df = pd.read_csv(
                f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv",
                encoding='utf-8',
                decimal=',',
                usecols=colunas,
                low_memory=False
                )
            
            # 2. Divide a coluna 'Ano e mês de lançamento' em duas novas: 'ano' e 'mes'
            df[['Ano', 'Mes']] = df['Ano e mês do lançamento'].str.split('/', expand=True)

            # 3. (Opcional) Converter para inteiros, já que no banco usamos INT
            df['Ano'] = df['Ano'].astype(int)
            df['Mes'] = df['Mes'].astype(int)

            df['Valor Empenhado (R$)'] = df['Valor Empenhado (R$)'].astype(float)
            df['Valor Liquidado (R$)'] = df['Valor Liquidado (R$)'].astype(float)
            df['Valor Pago (R$)'] = df['Valor Pago (R$)'].astype(float)

            # 4. Agora você pode remover a coluna original se não for mais usar
            df = df.drop(columns=['Ano e mês do lançamento'])

            os.makedirs("dados_json", exist_ok=True)
            os.makedirs(f"dados_json/dados_{ano}_json", exist_ok=True)
            df.to_json(f"dados_json/dados_{ano}_json/dados_{ano}{mes:02d}.json", orient='records')

            print(f"{mes} de {ano} salvo!")