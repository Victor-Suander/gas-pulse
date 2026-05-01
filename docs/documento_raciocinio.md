# Documento de Raciocinio - FuelSync

## 1. Entendimento do problema

O case da Bridge & Co. apresenta uma situacao comum em operacoes distribuidas: dados relevantes existem, mas estao espalhados em arquivos diferentes, enviados por filiais diferentes e com formatos que exigem padronizacao antes da analise.

No contexto da rede ficticia de postos, cada filial envia arquivos CSV de vendas e relatos em TXT escritos pelos gerentes. Os CSVs trazem valores de venda, mas os nomes dos produtos podem aparecer de formas inconsistentes. Os relatos dos gerentes trazem informacoes qualitativas importantes, como alertas, destaques e percepcao operacional, mas esse conteudo precisa ser resumido para apoiar decisao.

O problema central, portanto, e transformar dados dispersos em uma visao consolidada, confiavel e facil de revisar pela sede.

## 2. Objetivo da solucao

O FuelSync foi construido para automatizar esse fluxo e entregar uma base clara para tomada de decisao.

A solucao transforma os arquivos enviados em:

- vendas consolidadas;
- volume estimado vendido em litros;
- resumo estruturado dos relatos dos gerentes;
- alertas operacionais;
- ranking de desempenho por filial e por produto;
- corpo de e-mail sugerido para envio a sede;
- arquivos finais em CSV;
- PDF gerado sob demanda;
- copia organizada dos resultados em uma pasta local de exportacao.

O objetivo nao foi criar uma plataforma grande ou complexa, mas sim uma aplicacao simples, explicavel e robusta para o escopo do case.

## 3. Estrategia adotada

A estrategia foi separar o que precisa ser deterministico do que pode se beneficiar de IA.

Para dados estruturados, como filial, produto, preco, volume e ranking, usei regras explicitas no codigo. Isso reduz ambiguidade e torna o resultado auditavel.

Para textos narrativos dos gerentes, usei Gemini API para gerar resumo, destaques, alertas e sentimento geral. Esse e o ponto em que a IA agrega valor, porque o conteudo e qualitativo e pode variar bastante.

As principais escolhas tecnicas foram:

- Flask para criar uma interface web simples e objetiva;
- pandas para leitura, validacao e consolidacao dos dados tabulares;
- requests e BeautifulSoup para coletar precos de referencia via web;
- regras deterministicas para normalizacao de produtos e identificacao de filiais;
- Gemini API apenas para analise dos relatos dos gerentes;
- CSV como formato principal de entrega;
- PDF sob demanda como complemento para apresentacao;
- exportacao local em `Documents/FuelSync/` para facilitar acesso aos arquivos finais.

## 4. Fluxo de dados

O fluxo da aplicacao segue esta ordem:

1. O usuario envia CSVs de vendas e TXTs com relatos dos gerentes.
2. O sistema salva e valida os arquivos recebidos.
3. Os precos de referencia sao coletados da URL oficial do case.
4. Os produtos sao normalizados para nomes canonicos.
5. As vendas sao consolidadas em uma base unica.
6. O volume estimado em litros e calculado.
7. Os e-mails dos gerentes sao resumidos com IA ou fallback local.
8. O ranking por filial e por produto e gerado.
9. A interface exibe o relatorio visual e o corpo de e-mail sugerido.
10. O PDF pode ser gerado sob demanda pelo usuario.
11. Os resultados sao exportados para uma pasta datada em `Documents/FuelSync/`.

Esse fluxo procura manter a automacao ponta a ponta, mas sem esconder do usuario os principais artefatos gerados.

## 5. Normalizacao dos produtos

Os produtos vendidos podem aparecer com variacoes de nome. Para evitar que isso gere duplicidade ou erro no calculo, a aplicacao normaliza os nomes para tres produtos canonicos:

- Gasolina Comum;
- Etanol;
- Diesel S10.

Exemplos de variacoes tratadas:

- `GC`, `Gas. Comum`, `Gasolina` e `Gasolina C` sao mapeados para `Gasolina Comum`;
- `Etanol Hidratado`, `Etanol Hid.` e `Etanol Comum` sao mapeados para `Etanol`;
- `Diesel S-10`, `DSL S10` e `S10` sao mapeados para `Diesel S10`.

Essa etapa nao usa IA. Ela e feita por regra deterministica, porque o mapeamento de produto precisa ser previsivel, repetivel e facil de auditar.

Quando aparece um produto desconhecido, o processamento gera erro claro em vez de assumir um mapeamento incerto.

## 6. Identificacao das filiais

A filial e identificada pelo codigo presente no nome do arquivo:

- `F001`;
- `F002`;
- `F003`;
- `F004`;
- `F005`.

Esses codigos sao resolvidos por um mapa fixo de filiais. A aplicacao espera nomes como:

- `vendas_F001_marco2025.csv`;
- `email_F001_marco2025.txt`.

Essa escolha evita depender de IA ou de texto livre para identificar filial. Como filial e uma regra estrutural do dado, ela deve ser extraida de forma deterministica.

## 7. Coleta de precos

A aplicacao consulta automaticamente a URL oficial do case para obter os precos medios de referencia:

```text
https://bridgenoc.github.io/case-postos/precos_marco2025.html
```

Para aumentar a robustez da coleta, a requisicao usa headers com `User-Agent`, timeout e tentativas com espera progressiva.

A prioridade e:

```text
web -> cache recente -> fallback padrao do case
```

Quando a URL responde corretamente, os precos coletados sao usados e o cache interno e atualizado em:

```text
app/cache/precos_referencia_marco2025.json
```

Se a URL falhar, a aplicacao tenta usar esse cache, desde que ele esteja integro, contenha os tres produtos obrigatorios e tenha sido atualizado ha no maximo 24 horas.

Se a URL falhar e nao houver cache valido, a aplicacao usa o fallback padrao do case:

```text
Gasolina Comum: 6.29
Etanol: 4.11
Diesel S10: 6.54
```

A interface informa quando cache ou fallback sao usados, para que a resiliencia nao fique escondida do usuario.

## 8. Calculo do volume estimado

Os arquivos de venda trazem o valor total em reais, mas nao trazem diretamente o volume vendido em litros. Por isso, o volume e estimado a partir do preco medio por litro.

A formula usada e:

```text
volume_estimado_litros = valor_total_brl / preco_medio_litro_brl
```

Esse calculo permite comparar produtos e filiais tambem em termos de volume estimado, nao apenas faturamento.

O valor e uma estimativa porque usa preco medio de referencia, e nao necessariamente o preco exato de cada venda individual.

## 9. Uso da IA

A Gemini API e usada apenas para interpretar os relatos dos gerentes.

Para cada e-mail, a IA deve retornar um JSON estruturado com:

- resumo;
- destaques;
- alertas;
- sentimento geral.

A IA nao e usada para:

- identificar filial;
- normalizar produto;
- calcular vendas;
- calcular volume;
- definir preco;
- decidir pasta, mes ou regra de negocio.

Essa separacao foi intencional. Dados estruturados e numericos devem seguir regras deterministicas. A IA entra apenas onde ha texto narrativo e interpretacao qualitativa.

Se a Gemini API falhar, estiver indisponivel ou atingir limite de cota, a aplicacao usa fallback local baseado em heuristicas simples. Assim, o fluxo continua funcionando mesmo sem resposta da API.

## 10. Tratamento de erros e resiliencia

A aplicacao inclui tratamentos para evitar que falhas comuns interrompam a entrega sem explicacao.

Foram considerados:

- validacao de extensoes permitidas para upload;
- verificacao de colunas obrigatorias nos CSVs;
- erro claro para produto desconhecido;
- erro claro para nome de arquivo fora do padrao esperado;
- retry na coleta da URL de precos;
- cache recente para reduzir impacto de falha temporaria da URL;
- fallback padrao do case quando a URL e o cache falham;
- fallback local para resumo dos e-mails quando a IA falha;
- limpeza de `output/` ao iniciar a aplicacao;
- exportacao organizada em pasta datada dentro de `Documents/FuelSync/`.

O objetivo foi manter o fluxo previsivel e apresentar mensagens compreensiveis para o usuario.

## 11. Arquivos gerados

Durante a execucao, a aplicacao usa tres tipos de pasta com responsabilidades diferentes.

`output/` e a pasta local de execucao. Ela e ignorada no Git e e limpa ao iniciar a aplicacao para evitar confusao com arquivos antigos.

`app/cache/` guarda o cache interno de precos. Essa pasta tambem e ignorada no Git, porque cache nao e entrega do usuario.

`docs/resultados/marco2025/` contem exemplos finais versionados no GitHub, usados para demonstrar a saida esperada do projeto.

Os principais arquivos gerados sao:

- `vendas_consolidadas_marco2025.csv`;
- `resumo_gerentes_marco2025.csv`;
- `ranking_faturamento_marco2025.csv`;
- `relatorio_consolidado_marco2025.pdf`.

Ao processar os arquivos, os tres CSVs sao gerados em `output/` e copiados para uma pasta datada em:

```text
Documents/FuelSync/marco2025_YYYY-MM-DD_HHhMMmSSs/
```

O PDF e gerado somente quando o usuario clica em `Gerar PDF`. Nesse momento, ele e salvo em `output/` e copiado para a mesma pasta da execucao atual.

## 12. Decisoes tecnicas

As principais decisoes tecnicas foram:

- usar Flask pela simplicidade e rapidez para criar uma interface web funcional;
- usar pandas pela eficiencia no tratamento de dados tabulares;
- usar requests e BeautifulSoup para cumprir a coleta automatica de precos via web;
- manter regras deterministicas para tudo que envolve dados estruturados;
- usar IA apenas para texto narrativo, onde ela realmente agrega valor;
- gerar CSVs para facilitar validacao manual e reuso em planilhas;
- gerar PDF sob demanda para evitar criar arquivo desnecessario antes da decisao do usuario;
- exportar os arquivos para `Documents/FuelSync/` para facilitar a localizacao dos resultados.

Essas escolhas mantem a solucao simples, mas com boa separacao entre automacao, confiabilidade e experiencia de uso.

## 13. Limitacoes conhecidas

Algumas limitacoes foram mantidas conscientemente para preservar o escopo do case:

- o projeto esta focado em marco/2025;
- nao possui autenticacao de usuarios;
- nao possui banco de dados;
- nao envia e-mail automaticamente;
- a Gemini API depende de chave e cota disponivel;
- o fallback local da IA e mais simples que a analise feita pela Gemini;
- suporte dinamico a meses futuros ainda nao foi implementado.

## 14. Proximos passos

Possiveis evolucoes:

- suporte dinamico a outros meses;
- envio automatico de e-mail apos revisao do usuario;
- dashboard com graficos e filtros;
- download direto dos arquivos pela interface;
- persistencia em banco de dados;
- mais testes automatizados para servicos e fluxos de erro;
- deploy em ambiente web;
- melhoria do PDF com mais indicadores e comparativos.

## 15. Como eu defenderia a solucao na entrevista

Eu defenderia o FuelSync como uma solucao simples, objetiva e pensada para confiabilidade.

Minha prioridade foi separar bem as responsabilidades. Tudo que envolve regra de dado, como filial, produto, preco, volume e ranking, foi tratado de forma deterministica. Isso torna o resultado previsivel e auditavel.

A IA foi usada apenas onde ela faz sentido: interpretar relatos narrativos dos gerentes. Mesmo assim, o fluxo nao depende totalmente dela, porque existe fallback local caso a API falhe ou esteja sem cota.

Tambem me preocupei com resiliencia. A coleta de precos tenta primeiro a web, depois usa cache recente e, por ultimo, fallback padrao do case. Isso evita que uma falha temporaria de rede impeça o processamento.

Outro ponto importante foi organizar os artefatos. Separei arquivos de execucao (`output/`), cache interno (`app/cache/`) e exemplos versionados (`docs/resultados/marco2025/`). Alem disso, a exportacao em `Documents/FuelSync/` facilita a vida de quem precisa encontrar e conferir os resultados finais.

No geral, a solucao busca equilibrar automacao ponta a ponta, clareza de raciocinio e senso pratico de produto.
