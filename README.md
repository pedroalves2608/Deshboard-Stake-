📊 Dashboard de Frequência – Estaca Florianópolis

Ferramenta para consolidar, processar e visualizar frequência das alas da Estaca Florianópolis usando PDFs exportados semanalmente do site da Igreja.

📁 Estrutura do Projeto
Projeto Estaca/
│
├── dashboard_frequencia_estaca.py      # Dashboard Streamlit
├── processar_pdfs.py                   # Script offline para extrair dados dos PDFs
│
├── /data
│   ├── /pdf_raw
│   │     └── /2025                     # PDFs semanais (1 PDF por ala)
│   │          ├── arquivo1.pdf
│   │          ├── arquivo2.pdf
│   │          └── ...
│   │
│   └── /output
│         └── frequencia_estaca_2025.csv   # CSV consolidado gerado pelo script
│
└── README.md

🚀 Fluxo de Uso

Este projeto funciona em duas etapas:

1) Processar os PDFs (offline, antes do dashboard)

Toda sexta-feira:

Acesse o site da Igreja

Exporte os PDFs de frequência das alas (um PDF por ala)

Salve todos os PDFs em:

data/pdf_raw/2025/


Rode o processador:

Windows (PowerShell)
& "C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python313\python.exe" processar_pdfs.py


Ou simplesmente:

python processar_pdfs.py


O script irá:

✔ Ler todos os PDFs
✔ Identificar as bolinhas por pessoa
✔ Contar presenças
✔ Agrupar por data (ex: “9 nov”, “16 nov”…)
✔ Detectar nomes das alas
✔ Criar o CSV final:

data/output/frequencia_estaca_2025.csv

2) Executar o Dashboard

Depois que o CSV existir:

streamlit run dashboard_frequencia_estaca.py


O dashboard permite:

Filtrar alas

Selecionar intervalos de semanas

Ver gráficos de linha por ala

Frequência empilhada total

Mapa de calor

Boxplot por alas

Participação percentual na estaca

Estatísticas gerais

🧠 Como funciona a leitura dos PDFs

O script utiliza:

✔ pdfplumber

Detecta curvas preenchidas (as bolinhas)

Localiza datas automaticamente no cabeçalho

Calcula a linha de cada membro com base no Y (eixo vertical)

Agrupa as bolinhas por pessoa

Cada linha vale 1 presença por data, mesmo que hajam múltiplas bolinhas

✔ Agrupamento por linha

Bolinhas numa mesma linha podem estar a alguns pixels de distância — o script agrupa usando tolerância:

tolerância = 3px

✔ Resultado final por PDF da ala
{"9 nov": 42, "16 nov": 12, "23 nov": 36, "30 nov": 10}

🗂 Organização dos PDFs

Cada PDF deve estar com nome simples, por exemplo:

2025-11-30_frequencia_Agronomica.pdf
2025-11-30_frequencia_Ingleses.pdf
2025-11-30_frequencia_Rio_Vermelho.pdf


O script automaticamente extrai o nome da ala lendo a primeira linha do PDF.

🔧 Requisitos
pip install streamlit pdfplumber pandas matplotlib numpy

🔄 Atualizando semanalmente

Toda sexta:

Baixe os PDFs da semana

Coloque em /data/pdf_raw/2025/

Rode:

python processar_pdfs.py


Depois:

streamlit run dashboard_frequencia_estaca.py


E o dashboard será atualizado automaticamente.

🆘 Dúvidas Comuns
❓ O dashboard não abre

➡ Provavelmente o CSV ainda não existe.
Rode: python processar_pdfs.py.

❓ Os números parecem errados

➡ Certifique-se de que:

O PDF é o oficial exportado pelo site (não digitalizado)

Não está corrompido

O layout não foi alterado

❓ O CSV está ocupado (erro PermissionDenied)

➡ Feche o arquivo no Excel antes de rodar o script.

📌 Licença

Uso pessoal no ambiente da Estaca Florianópolis.