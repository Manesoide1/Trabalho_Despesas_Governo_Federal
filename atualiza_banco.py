import controla_bd
try:
    print("Tentando atualização incremental...")
    controla_bd.atualiza_banco_de_dados()
    print("Atualização concluída com sucesso!")
    
except FileNotFoundError as e:
    print(f"\n[ALERTA] Arquivo crítico não encontrado: {e}")
    print("Iniciando recuperação total (Reset do Banco)...")
    controla_bd.reseta_banco_de_dados()
    print("Recuperação concluída!")
    
except Exception as e:
    # Caso ocorra qualquer outro erro (conexão, SQL, etc)
    print(f"\n[ERRO FATAL] Ocorreu um problema inesperado: {e}")