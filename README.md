# FuelSync

Aplicação web em Python/Flask para consolidação e análise de vendas de redes de postos de combustível, desenvolvida para o case técnico da Bridge & Co.

O FuelSync transforma arquivos CSV de vendas, relatos em TXT dos gerentes e preços de referência em arquivos consolidados, rankings, resumo operacional e PDF sob demanda.

## Contexto do case

A solução foi criada para automatizar uma rotina de análise da sede de uma rede fictícia de postos. O fluxo central recebe arquivos enviados por filiais, normaliza dados inconsistentes, consulta preços médios de referência e gera entregáveis prontos para revisão.

## Funcionalidades

- Upload de arquivos CSV de vendas.
- Upload de arquivos TXT com e-mails/relatos dos gerentes.
- Identificação determinística da filial pelo nome do arquivo.
- Normalização determinística dos produtos vendidos.
- Coleta automática de preços de referência via web.
- Cache local dos últimos preços válidos por até 24 horas.
- Fallback padrão do case quando a URL falha e não há cache válido.
- Cálculo de volume estimado em litros.
- Consolidação das vendas em CSV.
- Uso da Gemini API apenas para resumir textos narrativos dos gerentes.
- Fallback local para resumo de e-mails quando a IA falha ou atinge limite de cota.
- Geração de ranking por filial e por produto.
- Geração de corpo de e-mail para envio à sede.
- Geração de PDF sob demanda, sem substituir os CSVs.

## Tecnologias utilizadas

- Python
- Flask
- pandas
- requests
- BeautifulSoup
- Gemini API
- python-dotenv
- ReportLab
- HTML/CSS/JavaScript

## Fluxo da aplicação

1. O usuário envia CSVs de vendas e TXTs de e-mails pela interface web.
2. A aplicação salva os arquivos enviados nas pastas de entrada.
3. As filiais são identificadas pelo padrão dos nomes dos arquivos.
4. Os produtos são normalizados para os nomes canônicos do case.
5. Os preços médios são coletados da URL do case.
6. Se a URL falhar, o sistema tenta usar cache recente; se não houver cache válido, usa fallback padrão.
7. As vendas são consolidadas e o volume estimado é calculado.
8. Os e-mails são resumidos com Gemini API ou fallback local.
9. O ranking de faturamento é gerado.
10. A interface exibe relatório consolidado, corpo de e-mail e botão para gerar PDF sob demanda.

## Coleta de preços

A URL usada como fonte principal é:

```text
https://bridgenoc.github.io/case-postos/precos_marco2025.html
```

A prioridade é:

```text
web -> cache recente -> fallback padrão do case
```

O cache local é salvo em:

```text
output/precos_referencia_marco2025.json
```

O cache só é usado quando está íntegro, contém os três produtos obrigatórios e foi atualizado há no máximo 24 horas.

Fallback padrão do case:

```python
{
    "Gasolina Comum": 6.29,
    "Etanol": 4.11,
    "Diesel S10": 6.54,
}
```

## Entradas esperadas

Arquivos de vendas:

```text
vendas_F001_marco2025.csv
vendas_F002_marco2025.csv
...
vendas_F005_marco2025.csv
```

Arquivos de e-mails:

```text
email_F001_marco2025.txt
email_F002_marco2025.txt
...
email_F005_marco2025.txt
```

O código `F001`, `F002`, etc. é extraído do nome do arquivo e resolvido por um mapa fixo de filiais.

## Normalização de produtos

| Produto canônico | Variações aceitas |
|---|---|
| Gasolina Comum | Gasolina Comum, Gas. Comum, Gasolina Comun, Gasolina, Gasolina C, GC |
| Etanol | Etanol, Etanol Hidratado, Etanol Hid., Etanol Comum |
| Diesel S10 | Diesel S10, Diesel S-10, Diesel S10 Aditivado, DSL S10, S10 |

Produtos desconhecidos geram erro claro. A IA não é usada para normalizar produtos.

## Uso de IA

A Gemini API é usada somente para:

- resumir e-mails dos gerentes;
- identificar destaques;
- identificar alertas;
- classificar sentimento geral.

A chave é carregada por variável de ambiente:

```text
GEMINI_API_KEY=sua_chave_aqui
```

O arquivo `.env` não deve ser versionado. Ele já está incluído no `.gitignore`.

A IA não é usada para identificar filial, normalizar produtos, calcular valores, decidir preços ou definir mês/pasta.

## Arquivos gerados

Durante a execução, a aplicação gera arquivos em `output/`:

```text
output/vendas_consolidadas_marco2025.csv
output/resumo_gerentes_marco2025.csv
output/ranking_faturamento_marco2025.csv
output/relatorio_consolidado_marco2025.pdf
output/precos_referencia_marco2025.json
```

O diretório `output/` é ignorado pelo Git porque contém saídas locais geradas pela aplicação.

Exemplos versionados dos resultados finais ficam em:

```text
docs/resultados/marco2025/
```

## Colunas principais

`vendas_consolidadas_marco2025.csv`:

- `data`
- `filial_id`
- `filial_nome`
- `produto_canonico`
- `valor_total_brl`
- `preco_medio_litro_brl`
- `volume_estimado_litros`

`resumo_gerentes_marco2025.csv`:

- `filial_id`
- `filial_nome`
- `resumo`
- `destaques`
- `alertas`
- `sentimento_geral`

## PDF sob demanda

O PDF é gerado pela interface somente quando o usuário clica em `Gerar PDF`.

Se o arquivo `output/relatorio_consolidado_marco2025.pdf` já existir, a aplicação não sobrescreve o arquivo e exibe um aviso para usar o PDF existente ou removê-lo antes de gerar novamente.

## Estrutura do projeto

- `app/` - aplicação Flask.
- `app/routes.py` - rotas e orquestração do fluxo web.
- `app/services/` - processamento de vendas, e-mails, preços e relatórios.
- `app/utils/` - normalização, filiais e utilitários de arquivos.
- `app/templates/` - templates HTML.
- `app/static/` - estilos CSS.
- `vendas/` - arquivos CSV de entrada.
- `emails/` - arquivos TXT de entrada.
- `output/` - arquivos gerados localmente, ignorados pelo Git.
- `docs/resultados/marco2025/` - exemplos versionados de saída.
- `tests/` - testes automatizados.

## Como executar

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Acesse:

```text
http://127.0.0.1:5000
```

## Configuração do .env

Crie um arquivo `.env` na raiz do projeto:

```text
GEMINI_API_KEY=sua_chave_aqui
```

Não coloque a chave real no repositório.

## Tratamento de erros

O FuelSync trata:

- ausência de arquivos;
- extensão inválida;
- CSV com colunas obrigatórias ausentes;
- produto desconhecido;
- filial fora do padrão esperado;
- falha temporária na URL de preços;
- cache de preços ausente, inválido ou vencido;
- falha ou limite da Gemini API;
- tentativa de gerar PDF antes do processamento.

## Decisões técnicas

- Flask foi escolhido por simplicidade e agilidade para o protótipo web.
- pandas centraliza manipulação tabular e geração dos CSVs.
- requests e BeautifulSoup fazem a coleta automática dos preços.
- Regras determinísticas cuidam de filiais, produtos, preços e cálculos.
- IA é aplicada apenas onde há texto narrativo e ambiguidade humana.
- CSVs permanecem como entregáveis principais do case.
- PDF é uma entrega complementar sob demanda.

## Limitações conhecidas

- Não há autenticação de usuários.
- Não há banco de dados relacional.
- O upload sobrescreve arquivos com mesmo nome nas pastas de entrada.
- O fallback local da IA é heurístico e mais simples que a análise da Gemini.
- O PDF é um resumo complementar e não substitui os CSVs.

## Próximos passos

- ampliar testes automatizados;
- permitir download direto dos arquivos gerados;
- enriquecer o PDF com mais detalhes do relatório visual;
- adicionar gráficos e filtros;
- preparar deploy em ambiente web.

## Autor

Desenvolvido por Victor-Suander.
