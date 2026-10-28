EstoqueLab

Aplicação web para controle de estoque de reagentes de laboratório, feita com Python e Streamlit, usando o Google Sheets como base de dados.

Status: projeto de portfólio (protótipo). Foi inspirado na rotina de controle de reagentes em laboratórios de análises clínicas e ainda não foi usado em um laboratório real. Use apenas com dados de estoque, nunca com dados de pacientes.

O problema

Em laboratórios, o controle de lotes, validades e consumo de reagentes costuma ficar em planilhas soltas, sem histórico de quem retirou o quê e sem aviso de estoque baixo ou lote perto do vencimento. O EstoqueLab reúne esse controle em uma interface simples, com registro de cada retirada e indicadores para apoiar a reposição.

Funcionalidades
Login com perfis de acesso: usuários e senhas ficam na aba usuarios da planilha. O perfil admin tem acesso ao cadastro de lotes; os demais usuários registram retiradas e consultam os painéis.
Dashboard: indicadores de total de lotes, lotes com estoque baixo (quantidade igual ou abaixo do mínimo) e lotes com validade em até 30 dias; gráfico de estoque por reagente e gráfico de consumo acumulado ao longo do tempo (Plotly).
Cadastro (admin): nome, lote, quantidade, estoque mínimo, validade e status de validação (Aprovado, Pendente ou Reprovado).
Retirada: escolha do item por nome e lote, com validação da quantidade disponível. Cada retirada é gravada no histórico com data e usuário, e o lote é removido da lista quando a quantidade chega a zero.
Relatórios: tabela com o histórico de retiradas e download em CSV.
Tecnologias

Python, Streamlit, Pandas, Plotly, gspread e google-auth (conta de serviço do Google).

Como rodar
Clone o repositório e instale as dependências:
bash
   pip install -r requirements.txt
Crie uma planilha no Google Sheets com três abas e estas colunas na primeira linha:
Aba	Colunas
estoque	nome, lote, quantidade, minimo, status_validacao, validade
historico	nome, lote, quantidade_retirada, data, usuario
usuarios	usuario, senha, tipo (use admin para administradores)
Crie uma conta de serviço no Google Cloud, ative as APIs Google Sheets e Google Drive e compartilhe a planilha com o e-mail da conta de serviço.
Crie o arquivo .streamlit/secrets.toml com os campos da chave da conta de serviço, sob a seção [gcp_service_account]. Nunca envie esse arquivo ou a chave JSON ao repositório.
No app.py, troque o valor de SHEET_ID pelo ID da sua planilha (o trecho da URL entre /d/ e /edit).
Execute:
bash
   streamlit run app.py
Limitações conhecidas
As senhas ficam em texto puro na planilha. Para uso real, é preciso armazenar hashes (por exemplo, com bcrypt) ou usar uma biblioteca de autenticação.
O app está preso a uma única planilha, definida no código (SHEET_ID).
Não há cache: a cada interação a planilha é lida de novo, o que pode esbarrar nos limites da API do Google.
O indicador "vencendo" também conta lotes que já venceram.
A retirada não bloqueia lotes com status "Reprovado".
Não há controle para dois usuários alterando o mesmo lote ao mesmo tempo.
Próximos passos
Modo multi-laboratório: permitir que cada laboratório use o app com o seu próprio estoque, sem editar o código (por exemplo, conectando a própria planilha ou importando um CSV direto no navegador).
Armazenar senhas com hash e revisar a autenticação.
Usar cache nas leituras e tratar concorrência.
Separar "vencidos" de "a vencer" e bloquear retirada de lotes reprovados.
Alertas de reposição e publicação de uma demonstração online com dados simulados.
Testes automatizados.
Autor

Matheus Moreira Gomes, biomédico, mestrando em Ciências Médicas (FMUSP) e MBA em Inteligência Artificial e Ciência de Dados na Saúde (PUCRS). LinkedIn
