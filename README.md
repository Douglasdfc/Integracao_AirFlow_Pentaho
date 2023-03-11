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

