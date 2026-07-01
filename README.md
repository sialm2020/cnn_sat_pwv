# Classificação automática de gatilhos PWV-GNSS Jump usando GOES-16

Este repositório contém os arquivos utilizados na atividade técnica sobre fontes de dados, redes neurais MLP e CNN, aplicada ao problema de classificação automática de gatilhos PWV-GNSS Jump com apoio de imagens de satélite geoestacionário.

## Objetivo

O objetivo da atividade é apresentar uma prova de conceito para automatizar a interpretação de gatilhos da técnica PWV-GNSS Jump no entorno da antena GNSS do sítio ATTO/Campina, na Amazônia Central.

A proposta considera a combinação entre:

- séries temporais de vapor d'água precipitável estimado por GNSS;
- imagens infravermelhas do satélite GOES-16;
- atributos físicos e geométricos de objetos frios identificados nas imagens;
- técnicas de aprendizado profundo, especialmente MLP e CNN.

## Dados utilizados

Neste estágio, o repositório contém uma amostra piloto composta por uma imagem GOES-16 em formato NetCDF.

O arquivo NetCDF é utilizado para demonstrar as seguintes etapas:

1. leitura da imagem de satélite;
2. conversão para temperatura de brilho;
3. recorte espacial no entorno da antena GNSS;
4. identificação de pixels frios com Tb < 230 K;
5. segmentação de objetos frios;
6. extração de atributos como área, temperatura mínima e distância em relação à antena.

## Arquivos principais

- `process_image.ipynb`: notebook com o processamento da imagem GOES-16.
- `arq.nc`: arquivo NetCDF utilizado como amostra piloto.
- `README.md`: descrição do repositório e da atividade.

## Metodologia

A metodologia parte de uma imagem GOES-16 no canal infravermelho. A imagem é recortada no entorno da antena GNSS e analisada com base na temperatura de brilho. Pixels com temperatura de brilho inferior a 230 K são considerados candidatos a nuvens profundas.

Após a aplicação do limiar, regiões conectadas são agrupadas em objetos frios. Para cada objeto, são extraídos atributos como:

- área;
- temperatura de brilho mínima;
- distância mínima em relação à antena GNSS;
- posição relativa;
- relevância física para o gatilho PWV-GNSS Jump.

## Relação com MLP e CNN

A MLP é considerada como uma abordagem para dados tabulares. Nesse caso, a entrada da rede seria formada por atributos derivados do PWV e dos objetos frios identificados nas imagens.

A CNN é considerada como uma abordagem para dados espaciais. Nesse caso, a entrada da rede seria o próprio recorte da imagem GOES-16, permitindo que o modelo aprenda padrões espaciais associados à nebulosidade profunda.

Neste estágio, o trabalho não apresenta o treinamento final de uma rede neural, pois o conjunto de dados completo ainda está em construção. A contribuição principal é demonstrar o fluxo metodológico necessário para transformar dados GNSS e imagens GOES-16 em entradas adequadas para modelos MLP e CNN.

## Link do repositório

https://github.com/sialm2020/cnn_sat_pwv
