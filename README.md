# Projeto de Engenharia de Sistemas Distribuídos
Repositório para o projeto da disciplina de Engenharia de Sistemas Distribuídos

## Tema da equipe

POC 5 — Anti-Platform Throttling

Simular e medir estratégias de distribuição temporal de engajamento em plataformas externas, evitando throttling e penalizações algorítmicas.

Escopo:

- Simulação de volume de engajamento direcionado em ambiente controlado
- Distribuição temporal com jitter variável e rate limiting por conteúdo
- Medição de thresholds estimados por plataforma (YouTube, Instagram, TikTok)
- Fila inteligente: balanceamento de carga entre campanhas ativas
- Pool de conteúdos rotativos com múltiplas URLs por anunciante

Padrões Recomendados: Rate Limit/Throttling, Load Balancing, Queues/PubSub/Fanout, Traffic
Sharding, Bulkhead/Isolation, Circuit Breaker, Feature Flag

Decisões-Chave: Thresholds por plataforma, estratégia de distribuição, alertas e pausa
automática

## Integrantes da equipe

1. **BRUNO FORMIGA BRANDÃO**  
   Email: bruno.formiga@academico.ufpb.br

2. **CAMILA EDUARDO COSTA DE VASCONCELOS**  
   Email: camilaaeduardo@gmail.com

3. **ELIANE SANTOS SILVA**  
   Email: eliane.santos.silva@academico.ufpb.br

4. **GISELE SILVA GOMES**  
   Email: gisele.gomes@academico.ufpb.br

5. **KLAYVERT DE ANDRADE ARAÚJO**  
   Email: klayvert.andrade@academico.ufpb.br

6. **LUCAS RONDINELI LUCENA FRAGOSO**  
   Email: lucas.rondinele93@gmail.com

Link da Documentação Final do Projeto: https://docs.google.com/document/d/1qTWPjUGwfmtNu3PTfZMzSrYEmb-wL6ZAQY8ieAj0aK8/edit?usp=sharing

Link do Diagrama C4 - Nível 1 (Contexto): https://drive.google.com/file/d/1EyB3Ur0WEH_RajkteIIaMYCYXCROOUOc/view?usp=sharing

Link do Diagrama C4 - Nível 2 (Containers): https://drive.google.com/file/d/1WGRCEU0rvo9p7Xg-idEaHYl7zU7sjp8l/view?usp=sharing

## Como rodar o projeto

1. Abra o terminal na pasta do projeto.

2. Execute:
python main.py

3. Informe quantos workers deseja iniciar.

4. O sistema subirá via Docker Compose e o frontend abrirá automaticamente no navegador (http://localhost:5173).

5. Use o painel web para:
- Visualizar métricas em tempo real (Dashboard)
- Lançar campanhas de engajamento (Campanhas)
- Controlar feature flags e configurar o circuit breaker (Controles)
- Monitorar likes por vídeo e plataforma (Engajamento)


## Videocast

Link do videocast: 
https://drive.google.com/file/d/1nu9IL6ewcOp6eshMYDxU0twOFq2dPadX/view?usp=sharing