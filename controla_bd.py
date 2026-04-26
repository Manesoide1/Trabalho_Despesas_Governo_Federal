from datetime import datetime
import gc
import io
import zipfile
import mysql.connector
import pandas as pd
from datetime import datetime
import time
import os
import requests
import coleta_calcula

def conecta_banco_de_dados ():
    # Estabelece a conexão com o servidor
    config = {
        'user': 'python_postgres',
        'password': 'python_postgres',
        'host': 'localhost'
    }

    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    return conexao, cursor

def cria_banco_e_tabelas(cursor):
    # Criando o banco de dados, caso ele não exista.
    cursor.execute("CREATE DATABASE IF NOT EXISTS trabalho_data_cience")
    cursor.execute("USE trabalho_data_cience")

    #Criando tabelas do banco de dados, caso não existam.
    cursor.execute("CREATE TABLE IF NOT EXISTS despesas_governo_federal (" \
                    "codigo_identificador BIGINT NOT NULL PRIMARY KEY," \
                    "ano INT NOT NULL," \
                    "mes INT NOT NULL," \
                    "orgao_superior VARCHAR(255)," \
                    "valor_empenhado DECIMAL(18, 2)," \
                    "valor_liquidado DECIMAL(18, 2)," \
                    "valor_pago DECIMAL(18, 2)" \
                    ")")

    cursor.execute("CREATE TABLE IF NOT EXISTS soma_despesas_anuais_governo_federal (" \
                    "ano INT NOT NULL PRIMARY KEY," \
                    "valor_empenhado DECIMAL(18, 2)," \
                    "valor_liquidado DECIMAL(18, 2)," \
                    "valor_pago DECIMAL(18, 2)" \
                    ")")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS soma_despesas_anuais_por_orgao (" \
                    "ano INT NOT NULL," \
                    "orgao_superior VARCHAR(255) NOT NULL," \
                    "valor_empenhado DECIMAL(18, 2)," \
                    "valor_liquidado DECIMAL(18, 2)," \
                    "valor_pago DECIMAL(18, 2)," \
                    "PRIMARY KEY (ano, orgao_superior)" \
                    ")")

def preenche_ou_atualiza_tabela_despesas_governo_federal(conexao, cursor, ano_inicio = 2014):
    for ano in range(ano_inicio, datetime.now().year + 1):
        for mes in range(1, 13):
            try:
                df = pd.read_json(f"dados_json/dados_{ano}_json/dados_{ano}{mes:02d}.json")

                # Reordenamos o DF para garantir que o código identificador seja o PRIMEIRO
                # e que o resto siga a ordem do comando SQL
                colunas_ordenadas = [
                    'Numero_Identificador', 'Ano', 'Mes', 'Nome Órgão Superior', 
                    'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'
                ]
                
                # Verifique se os nomes das colunas acima batem EXATAMENTE com as chaves do seu JSON
                df = df[colunas_ordenadas]

                comando_sql = """INSERT INTO despesas_governo_federal 
                    (codigo_identificador, ano, mes, orgao_superior, valor_empenhado, valor_liquidado, valor_pago) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    valor_empenhado = VALUES(valor_empenhado),
                    valor_liquidado = VALUES(valor_liquidado),
                    valor_pago = VALUES(valor_pago)"""

                valores = list(df.itertuples(index=False, name=None))

                cursor.executemany(comando_sql, valores)
                
                #Salva tudo no banco de dados (Sem isso não salva nada)
                conexao.commit()
                print(f"{mes} de {ano} inserido em despesas_governo_federal!")
            except FileNotFoundError:
                print(f"Aviso: Arquivo dados_{ano}{mes:02d}.json não encontrado. Pulando...")
                continue
            except Exception as e:
                print(f"Erro ao processar dados_{ano}{mes:02d}.json: {e}")

def preenche_ou_atualiza_tabela_soma_despesas_anuais_governo_federal(conexao, cursor):
    df = pd.read_json("dados_despesas_anuais.json")

    # Reordenamos o DF para garantir que o código identificador seja o PRIMEIRO
    # e que o resto siga a ordem do comando SQL
    colunas_ordenadas = [
        'Ano', 'Valor Empenhado', 'Valor Liquidado', 'Valor Pago'
    ]
    
    # Verifique se os nomes das colunas acima batem EXATAMENTE com as chaves do seu JSON
    df = df[colunas_ordenadas]

    comando_sql = """INSERT INTO soma_despesas_anuais_governo_federal 
        (ano, valor_empenhado, valor_liquidado, valor_pago) 
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        valor_empenhado = VALUES(valor_empenhado),
        valor_liquidado = VALUES(valor_liquidado),
        valor_pago = VALUES(valor_pago)"""

    valores = list(df.itertuples(index=False, name=None))

    cursor.executemany(comando_sql, valores)
    
    #Salva tudo no banco de dados (Sem isso não salva nada)
    conexao.commit()
    print(f"Dados inseridos em soma_despesas_anuais_governo_federal!")

def preenche_ou_atualiza_tabela_soma_despesas_anuais_por_orgao(conexao, cursor, ano_inicio = 2014):
    for ano in range(ano_inicio, datetime.now().year + 1):
        df = pd.read_json(f"gastos_por_orgao_json/gasto_por_orgao_{ano}.json")

        # Reordenamos o DF para garantir que o código identificador seja o PRIMEIRO
        # e que o resto siga a ordem do comando SQL
        colunas_ordenadas = [
            'Nome Órgão Superior', 'Valor Empenhado (R$)', 'Valor Liquidado (R$)', 'Valor Pago (R$)'
        ]
        
        # Verifique se os nomes das colunas acima batem EXATAMENTE com as chaves do seu JSON
        df = df[colunas_ordenadas]

        comando_sql = """INSERT INTO soma_despesas_anuais_por_orgao 
            (orgao_superior, ano, valor_empenhado, valor_liquidado, valor_pago) 
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            valor_empenhado = VALUES(valor_empenhado),
            valor_liquidado = VALUES(valor_liquidado),
            valor_pago = VALUES(valor_pago)"""
        
        valores = [(row[0], ano, row[1], row[2], row[3]) for row in df.itertuples(index=False, name=None)]

        cursor.executemany(comando_sql, valores)
        
        #Salva tudo no banco de dados (Sem isso não salva nada)
        conexao.commit()
        print(f"Dados inseridos em soma_despesas_anuais_por_orgão!")

def deleta_banco(cursor):
    try:
        cursor.execute("DROP DATABASE IF EXISTS trabalho_data_cience")
        print("Banco de dados deletado.")
    except mysql.connector.Error as err:
        print(f"Erro ao deletar: {err}")

def desconecta_banco_de_dados(conexao, cursor):
    # Fecha a conexão inicial para reconectar ao banco específico
    cursor.close()
    conexao.close()

def reseta_banco_de_dados():
    conexao, cursor = conecta_banco_de_dados()

    deleta_banco(cursor)

    coleta_calcula.reseta_dados()

    conexao.ping(reconnect=True, attempts=3, delay=2)

    cria_banco_e_tabelas(cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_despesas_governo_federal(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_governo_federal(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_por_orgao(conexao, cursor)

def atualiza_banco_de_dados():
    conexao, cursor = conecta_banco_de_dados()

    coleta_calcula.atualiza_dados()

    conexao.ping(reconnect=True, attempts=3, delay=2)

    cria_banco_e_tabelas(cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_despesas_governo_federal(conexao, cursor, datetime.now().year)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_governo_federal(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_por_orgao(conexao, cursor, datetime.now().year)

def main():

    inicio = time.time()

    conexao, cursor = conecta_banco_de_dados()

    #deleta_banco(cursor)

    coleta_calcula.main()

    conexao.ping(reconnect=True, attempts=3, delay=2)

    cria_banco_e_tabelas(cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_despesas_governo_federal(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_governo_federal(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    preenche_ou_atualiza_tabela_soma_despesas_anuais_por_orgao(conexao, cursor)

    conexao.ping(reconnect=True, attempts=3, delay=2)

    query = "SELECT * FROM soma_despesas_anuais_governo_federal"

    df = pd.read_sql(query, conexao)

    coleta_calcula.gera_grafico_curvas_suaves(df, 'ano', ['valor_empenhado', 'valor_liquidado', 'valor_pago'], 'Evolução das depesas do Governo Federal')

    for ano in range(2014, datetime.now().year + 1):
        conexao.ping(reconnect=True, attempts=3, delay=2)

        query = f"SELECT orgao_superior, valor_empenhado, valor_liquidado, valor_pago FROM soma_despesas_anuais_por_orgao WHERE ano = {ano} ORDER BY valor_pago DESC"

        df = pd.read_sql(query, conexao).nlargest(10, 'Valor Pago (R$)')

        coleta_calcula.gera_grafico_pizza(df, 'valor_pago', 'orgao_superior', f'Distribuição de Gastos por Órgão em {ano} (Top 10)')

    desconecta_banco_de_dados(conexao, cursor)

    print(f"Tempo de execução: {time.time() - inicio:.2f} segundos.\nOu {(time.time() - inicio)//60:.2f} minutos e {(time.time() - inicio) % 60:.2f} segundos.")

#main()
