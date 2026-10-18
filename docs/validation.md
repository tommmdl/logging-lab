# O que foi colocado à prova

[English](validation.en.md) · [Voltar](../README.md)

O teste gera requisições reais da API com um marcador único, procura os registros no Loki e consulta o mesmo marcador através do Grafana. O acesso válido e o 404 esperado percorrem stdout do Gunicorn → API de logs do Kubernetes → Alloy → Loki → Grafana. A checagem do PostgreSQL usa uma mensagem `RAISE LOG`, sem alterar seus dados.

Também são verificados os labels, a ausência do marcador como label, o painel de quatro componentes e a preservação do datasource Prometheus e do painel de métricas. A troca do Pod do Loki confere registros anteriores e o mesmo PVC. As consultas de autorização verificam leitura de logs em notes-lab e negação de Secrets e de logs em monitoring-lab.

A [evidência local](../evidence/local-results.json) guarda horário UTC, versões, marcador e verificações aprovadas. A pipeline repete o teste em um cluster novo, com versões fixas dos projetos Kubernetes e monitoring-lab. Ela não instala Argo CD; o teste local usa o cluster em que ele já está presente.

A retenção de 24 horas é uma configuração, não um teste de duração executado. Não foram testados perda de nó, restauração de backup, carga, indisponibilidade longa, segurança contra um administrador do cluster ou entrega sem perda/repetição. Os logs permanecem em armazenamento local, com uma réplica. O teste não envia linhas diretamente à API de ingestão do Loki.

O resultado do GitHub Actions será acrescentado após a primeira execução.
