# Integracao_AirFlow_Pentaho
Com certeza há mais de uma forma de integrar o PDI (Pentaho Data Integration) com o Airflow, para que esse faça a orquestração do jobs e ktrs criados no PDI. 
Nesse artigo iremos ver uma forma simples, e que com certeza pode ser aprimorada para inserir mais etapas de controle das cargas ou de melhoria do processo, de como executar jobs usando o webserver do Airflow.

### Organizando a estrutura de pastas

O primeiro passo é organizar uma estrutura de pastas para que o processo fique bem organizado. 

Como você já deve saber, o Airflow precisa ser instalado em uma máquina Linux, então toda a estrutura de diretórios e comandos segue a lógica de uma máquina Linux.

Crie uma pasta na raiz do diretório chamada etl dentro dela crie mais duas pastas: jobs e temp_sh. Abra o terminal Linux e digite os seguintes comandos:

```bash
cd ~

mkdir etl

cd etl

mkdir jobs

mkdir temp_sh
```

Agora se você rodar o comando:

```bash
ls -l
```
será mostrada das duas pastas criadas nos comandos anteriores.

A pasta "jobs" receberá os arquivos .kjb e .ktr que você gerou quando criou os ETL's no PDI. 
A pasta "temp_sh" receberá os arquivos temporários criados pelo airflow que serão usados para executar os jobs. 

Agora podemos partir para construção do código em Python.


### Montando o código Python

A ideia é montar um código simples, sem a nessidade de instalação de plugins ou bibliotecas, então usaremos somente operadores nativos do Airflow, como PythonOperator e BashOperator.

Vamos explicar o código passo a passo:

Para começar, vamos importar as bibliotecas necessárias:

```python
import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

```
Abaixo iremos definir as variáveis necessárias para a execução da DAG.

* A variável "caminho_kitchen" recebe o caminho do arquivo "kitchen.sh" que está salvo na pasta do PDI, esse arquivo faz o disparo do job. (Caso você esteja executando uma transformação, usar o arquivo "pan.sh"
* A variável "caminho_kjb" recebe o caminho do arquivo .kjb que será executado, nesse exempplo o job se chama: "job_teste.kjb". Note que salvamos esse arquivo na pasta "jobs" que criamos dentro da pasta etl.
 * A variável "nome_arquivo_sh" recebe recebe o caminho e nome do arquivo temporário .sh que será criado para a execução do Airflow. Note que salvamos esse arquivo na pasta "tem_sh" que criamos dentro da pasta etl.
 * A variável "local" recebe recebe a informação de qual fuso horário o Airflow deve utilizar para executar o job, pois o horário padrão da ferramenta é UTC e no Brasil estamos em UTC-3.

```python
caminho_kitchen = "/home/douglas/opt/pdi-ce-9.3.0.0-428/data-integration/kitchen.sh" # Caminho do kitchen.sh (dentro da pasta raiz do PDI)
caminho_kjb = '/home/douglas/etl/jobs/job_teste.kjb' # Caminho do JOB que será executado
nome_arquivo_sh = "home/douglas/etl/temp_sh/teste.sh" # caminho do arquivo temporário que será chamdo pelo AirFlow
local = pytz.timezone("America/Sao_Paulo")

```
#### Definindo a DAG

Agora vamos definir a DAG:
```python
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

```
Aqui estamos definindo que a DAG começará a ser executada em 7 de março de 2023. 
Estamos definindo que não haverá novas tentativas de execução, em caso de erro, setando o argumento 'retries': 0, altere esse argumento caso haja a necessidade de tentar novas execuções
Estamos definindo o nome da DAG como "job_teste", esse é nome que aparecerá no painel de execuções do Airflow
E estamos definindo no argumento "schedule_interval" para que a DAG seja executada todos os dias às 03:30 da manhã. Esse argumento usa o padrão Crontab, que pode ser entendido melhor [aqui](https://crontab.guru/) ou [aqui](https://crontab.cronhub.io/)


#### Definindo as Tasks
A lógica de excução será a seguinte:

Um ETL criado no PDI pode ser executado, sem abrir a sua interface gráfica, executando um arquivo em formato .sh contendo o caminho do kitchen (na execução de jobs) ou o do pan (na execução de ktr) e o caminho do job ou ktr que vamos executar.

Nesse exemplo, iremos executar um job chamado "job_teste.kjb", então o nosso arquivo terá o seguinte conteúdo:

```t
"/home/douglas/opt/pdi-ce-9.3.0.0-428/data-integration/kitchen.sh" /file:"/home/douglas/etl/jobs/job_teste.kjb"
```
Isso é suficiente para que o job seja executado. 

Então teremos 4 tasks:

- 1ª -> Cria o arquivo .sh
- 2ª -> Preenche o arquivo .sh
- 3ª -> Executa o arquivo .sh, o que fará rodar ao ETL criado no PDI
- 4ª -> Apaga o arquivo .sh

Note que o arquivo só existirá na pasta "temp_sh" enquanto o ETL estiver sendo executado, isso garantirá uma maior organização da estrutura de pasta, evitando que em pouco tempo tenhamos vários arquivos nessa pasta sem utilização. 

O código que define as Tasks fica dessa forma:

```python
# Task para preencher arquivo com os caminhos
    def preenche_arquivo():
        with open(nome_arquivo_sh, "w") as f
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
```

Agora temos que definir em que order as tasks devem ser executadas

fazemos isso com o seguinte código:

```python
cria_arquivo >> escreve_arquivo >> carga >> remove_arquivo
```

O código conpleto fica da seguinte forma:

```python
import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

caminho_kitchen = "/home/douglas/opt/pdi-ce-9.3.0.0-428/data-integration/kitchen.sh" # Caminho do kitchen.sh (dentro da pasta raiz do PDI)
caminho_kjb = '/home/douglas/etl/jobs/job_teste.kjb' # Caminho do JOB que será executado
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

# Task para preencher arquivo com os caminhos
    def preenche_arquivo():
        with open(nome_arquivo_sh, "w") as f
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
```

Salve esse código em um arquivo em formato .py na pasta "dags" que fica do diretório onde você exportou a variável de ambiente do Airflow, dessa forma, a DAG deve aparecer no painel de controle de execuções do Airflow e você pode conferir a execução do seu ETL criado no Pentaho Data Integration.