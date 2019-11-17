# _Scrapeando_ as estações meteorológicas de São Paulo
Neste projeto você obterá os dados das estações meteorológicas de São Paulo através do site: https://www.cgesp.org/v3/estacoes-meteorologicas.jsp . Seu _scraper_ deverá retornar um objeto JSON contendo os seguintes dados de **todas** as estações meteorológicas nas últimas 24 horas: 
- timestamp (convertido para epoch)
- chuva (mm)
- velocidade do vento (m/s)
- direção do vento (graus de arco 0-360º)
- temperatura (ºC)
- umidade relativa (%)
- pressão (mbar)

Exemplo de resultado esperado do crawler:
```json
{
  "Penha": [
    {
        "timestamp": 1542632400,
        "chuva": 1.2,
        "vel_vento": 3.01,
        "dir_vento": 8,
        "temp": 17.51,
        "umidadade_rel": 86.92,
        "pressao": 934.55
    },
    {
        "timestamp": 1542628800,
        "chuva": 1,
        "vel_vento": 0,
        "dir_vento": 26,
        "temp": 18.04,
        "umidadade_rel": 86.77,
        "pressao": 933.98
    }, 
    ... 
  ],
  "Perus": [
    {
        "timestamp": 1542632400,
        "chuva": 4,
        "vel_vento": 0.19,
        "dir_vento": 136,
        "temp": 18.22,
        "umidadade_rel": 92.31,
        "pressao": 929.58
    },
    {
        "timestamp": 1542628800,
        "chuva": 3.6,
        "vel_vento": 0,
        "dir_vento": 243,
        "temp": 17.84,
        "umidadade_rel": 93.14,
        "pressao": 929.56
    }, 
    ... 
  ],
  ...
}
```

## Instalação
_Obs.: Estaremos usando `python3.6` e `pip` neste projeto, certifique-se de preparar seu ambiente_

**0-** [Opcional] Crie um ambiente virtual e ative-o para evitar poluir seu ambiente de trabalho

```sh
python3 -m venv venv
source venv/bin/activate
```

**1-** Instale as dependências do projeto

```sh
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**2-** Execute o script com 

```
python3 src/weather_scraper.py > resultado.json
```

A saída de erros/secundária contém o log da execução, ela é automaticamente guardada em um arquivo em `/tmp/weather_scraper.log` com mensagens de nível _INFO_ para cima. Para configura-la modifique o arquivo `logger.py` ([logging doc](https://docs.python.org/3/library/logging.config.html)). Na linha 45: `'handlers': ['file', 'console']`, pode-se remover `'file'` para exibir só em _stderr_, ou mesmo remover `'console'`, para só registrar no arquivo.

## Dependências
- BeatifulSoup: Um ótimo _HTML parser_ para Python
- requests: lib para realizar HTTP requests

### Dependências sugeridas para devs
- pylint: Linter capaz de encontrar erros e padronizar estilo de código
- autopep8: Auto formatador de código
- pytest: Executa testes unitários

### Explicação da execução

**1-** É realizado uma requisição, usando `requests.get()`, para a página principal de onde retiramos a lista das estações meteorológicas com suas URLs com auxílio de `BeatifulSoup`.

**2-** Para cada estação fazemos uma requisição para um endereço que foi encontrado usando o console de desenvolvedor (presente no Firefox e Chrome) na aba de Rede. Esta URL era chamada sempre que uma nova estação era selecionada, e é dela que é recebida a tabela com as medições desejadas. Contudo há um detalhe importante: sobrescrever o cabeçalho da requisição com o par `'referer': URL_in`. Isto é necessário devido a uma restrição da URL, que só aceita chamadas internas, como pode ser visto ao tentar acessá-la diretamente no browser.

> Não é permitido acesso direto a essa página  
  Acesse a partir de http://www.saisp.br/

**3-** Por fim basta organizar estes dados em algumas estruturas básicas e formatá-los em json.

### Testes

Para rodar os testes basta executar na linha de comando, opcionalmente com o nome de um arquivo de testes:

```
pytest [nome_do_teste.py]
```

### Linter

Para avaliar a qualidade do código em um arquivo segundo o que foi definido em `.pylintrc`, execute
```
pylint nome_do_arquivo.py
```
