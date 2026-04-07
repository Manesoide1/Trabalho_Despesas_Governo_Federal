import pandas as pd
import requests
import zipfile
import io
import os
import gc
import time
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3

def coleta_dados_despesas(url, ano, mes):
    # Adicionamos um 'User-Agent' para evitar que o portal bloqueie a requisição automática
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

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
                        df = pd.read_csv(f, sep=";", encoding='latin-1', on_bad_lines='skip', low_memory=False)
                        
                # Criar pasta para salvar os dados, se não existir
                os.makedirs("dados", exist_ok=True)
                os.makedirs(f"dados/dados_{ano}", exist_ok=True)
                
                # Salvar localmente
                df.to_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", index=False, encoding='utf-8')
                
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
        df = pd.read_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", encoding='utf-8', decimal=',', usecols=[despesa], low_memory=False)
        total_despesas_mes = df[despesa].sum()
        total_despesas_ano = total_despesas_mes if mes == 1 else total_despesas_ano + total_despesas_mes
        del df
        gc.collect()
    return total_despesas_ano

def media_despesas_ano(ano, despesa):
    meses_somados = 0
    for mes in range(1, 13):
        if not os.path.exists(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"):
            continue
        df = pd.read_csv(f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv", encoding='utf-8', decimal=',', usecols=[despesa], low_memory=False)
        total_despesas_mes = df[despesa].sum()
        meses_somados += 1
        media_despesas_ano = total_despesas_mes if mes == 1 else media_despesas_ano + total_despesas_mes
        del df
        gc.collect()
    media_despesas_ano = media_despesas_ano / meses_somados if meses_somados > 0 else 0
    return media_despesas_ano

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

        df = pd.read_csv(caminho, encoding='utf-8', decimal=',', usecols=['Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'],low_memory=False)

        resumo_mes = df.groupby('Nome Órgão Superior').sum().reset_index()
        dfs_meses.append(resumo_mes)

        del df
        gc.collect()
    
    if not dfs_meses:
        return pd.DataFrame()  # Retorna um DataFrame vazio se nenhum dado foi encontrado
    
    df_ano = pd.concat(dfs_meses).groupby('Nome Órgão Superior').sum().reset_index()
    return df_ano

        


def gera_grafico(entrada, eixo_x, categoria, valor, titulo = "Gŕafico em Colunas"):

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

def gera_grafico_horizontal(entrada, eixo_x, categoria, valor, titulo = "Gŕafico em Colunas"):

    if isinstance(entrada, str):
        df = pd.read_json(entrada)
    elif isinstance(entrada, pd.DataFrame):
        df = entrada
    else:
        raise ValueError("Entrada deve ser um caminho para JSON ou um DataFrame")

    df_melted = df.melt(id_vars=eixo_x, var_name=categoria, value_name=valor)

    sns.barplot(data=df_melted, y=eixo_x, x=valor, hue=categoria, palette='viridis')
    plt.ylabel(eixo_x, fontsize=12)
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

def limpa_dados():
    for ano in range(2014, datetime.now().year + 1):
        for mes in range(1, 13):
            caminho = f"dados/dados_{ano}/dados_{ano}{mes:02d}.csv"
            if os.path.exists(caminho):
                os.remove(caminho)
                print(f"Arquivo {caminho} removido.")
            else:
                print(f"Arquivo {caminho} não encontrado.")

def main():
    inicio = time.time()

    print("Coleta dos dados...")
    for ano in range(2014, datetime.now().year + 1):
        for mes in range(1, 13):
            url = f"https://portaldatransparencia.gov.br/download-de-dados/despesas-execucao/{ano}{mes:02d}"
            coleta_dados_despesas(url, ano, mes)
    
    print(f"Tempo de execução da coleta: {time.time() - inicio:.2f} segundos")

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto total a cada ano...")
    df = gera_dfs(2015, 2025, soma_despesas_ano)
    json_path = salva_dados_json(df, "dados_despesas_anuais.js")
    salva_dados_sql(df, "dados_despesas_anuais.db")

    print(f"Maior valor empenhado:{df["Valor Empenhado"].max()} em {df.loc[df["Valor Empenhado"].idxmax(), "Ano"]}")
    print(f"Maior valor liquidado:{df["Valor Liquidado"].max()} em {df.loc[df["Valor Liquidado"].idxmax(), "Ano"]}")
    print(f"Maior valor pago:{df["Valor Pago"].max()} em {df.loc[df["Valor Pago"].idxmax(), "Ano"]}")
    print()
    print(f"Menor valor empenhado:{df["Valor Empenhado"].min()} em {df.loc[df["Valor Empenhado"].idxmin(), "Ano"]}")
    print(f"Menor valor liquidado:{df["Valor Liquidado"].min()} em {df.loc[df["Valor Liquidado"].idxmin(), "Ano"]}")
    print(f"Menor valor pago:{df["Valor Pago"].min()} em {df.loc[df["Valor Pago"].idxmin(), "Ano"]}")


    print(f"Tempo de processamento da evolução das despesas públicas: {time.time() - inicio:.2f} segundos")

    gera_grafico(json_path, 'Ano', 'Etapa de Despesa', 'Valor (R$)', f'Evolução Anual das Despesas Públicas ({df["Ano"].min()}-{df["Ano"].max()})')

    

    inicio = time.time()

    print("\n\n\n\n\n\n\n\n\n\nCalculando o gasto médio mensal a cada ano...")
    df = gera_dfs(2015, 2025, media_despesas_ano)
    json_path = salva_dados_json(df, "dados_despesas_medias_anuais.js")
    salva_dados_sql(df, "dados_despesas_medias_anuais.db")
    print(f"Tempo de cálculo da média mensal das despesas públicas: {time.time() - inicio:.2f} segundos")
    gera_grafico(json_path, 'Ano', 'Etapa de Despesa', 'Valor (R$)', f'Média Mensal das Despesas Públicas ({df["Ano"].min()}-{df["Ano"].max()})')

    ano_inicio = 2015
    ano_fim = 2025

    os.makedirs("gastos_por_orgao_js", exist_ok=True)
    os.makedirs("gastos_por_orgao_db", exist_ok=True)

    for ano in range(ano_inicio, ano_fim+1):
        inicio = time.time()
        print(f"\n\n\n\n\n\n\n\n\n\nCalculando o gasto por orgão para o ano de {ano}...")
        df = gera_dfs_por_orgao(ano).nlargest(10, 'Valor Pago (R$)')

        json_path = salva_dados_json(df, f"gastos_por_orgao_js/gasto_por_orgao_{ano}.js")
        salva_dados_sql(df, f"gastos_por_orgao_db/gasto_por_orgao_{ano}.db")

        print(f"Tempo total de execução: {time.time() - inicio:.2f} segundos")
        gera_grafico_horizontal(json_path, 'Nome Órgão Superior', 'Etapa de Despesa', 'Valor (R$)', f'Top 10 Órgãos com Maior Valor Pago em {ano}')

main()