import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

caminho_kitchen = '"/home/douglas/opt/pdi-ce-9.3.0.0-428/data-integration/kitchen.sh"' # Caminho do kitchen.sh (dentro da pasta raiz do PDI)
caminho_kjb = '"/home/douglas/etl/jobs/job_teste.kjb"' # Caminho do JOB que será executado
nome_arquivo_sh = "home/douglas/etl/temp_sh/teste.sh" # caminho do arquivo temporário que será chamdo pelo AirFlow
local = pytz.timezone("America/Sao_Paulo")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 7, tzinfo = local),
    'retries': 0,
}

with DAG(
    'job_teste',
    default_args=default_args,
    schedule_interval='30 3 * * *', # Run every day at 03:30
) as dag:
    

   # Task para criar arquivo vazio
    cria_arquivo = BashOperator(

        task_id="cria_arquivo",
        bash_command= f'touch "{nome_arquivo_sh}"',
    )

    # Task para preencher arquivo com os caminhos
    def preenche_arquivo():
        with open(nome_arquivo_sh, "w") as f:
            f.write(f'{caminho_kitchen} /file:{caminho_kjb}')
        

    escreve_arquivo = PythonOperator(

        task_id = 'escreve_arquivo',
        python_callable = preenche_arquivo
    )


    # Task para criar executar o arquivo .sh (responsável pela carga)
    carga = BashOperator(

        task_id="carga",
        bash_command= f'sh "{nome_arquivo_sh}"',

    )


    # Task para excluir arquivo
    def exclui_arquivo():
        os.remove(nome_arquivo_sh)


    remove_arquivo = PythonOperator(

        task_id = 'remove_arquivo',
        python_callable = exclui_arquivo
    )

    cria_arquivo >> escreve_arquivo >> carga >> remove_arquivo