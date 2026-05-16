# Playbook de Contenção de Incidentes de Segurança — ETIR/AGETIC/UFMS

## phishing
- Orientar o usuário a NÃO clicar em links ou baixar anexos do e-mail suspeito.
- Encaminhar o e-mail original (como anexo) para etir@agetic.ufms.br.
- Redefinir a senha da conta possivelmente comprometida via Passaporte UFMS.
- Ativar autenticação em dois fatores na conta afetada.
- Verificar regras de encaminhamento indevidas na caixa de e-mail do usuário.

## malware
- Isolar imediatamente o equipamento afetado da rede (desconectar cabo e desativar Wi-Fi).
- Não desligar o equipamento — preservar evidências em memória.
- Acionar o responsável técnico do sistema afetado e abrir chamado de prioridade alta.
- Executar varredura com antivírus atualizado em modo offline.
- Registrar processos, conexões ativas e arquivos recém-modificados antes de qualquer limpeza.

## ransomware
- Isolar IMEDIATAMENTE todos os equipamentos afetados da rede.
- Desconectar backups conectados localmente para evitar criptografia.
- NÃO pagar o resgate — acionar ETIR e Gestão antes de qualquer decisão.
- Preservar imagens de disco dos equipamentos afetados para análise forense.
- Identificar o vetor de entrada (e-mail, RDP, USB) e comunicar a liderança imediatamente.

## unauthorized_access
- Revogar imediatamente as credenciais suspeitas via Passaporte UFMS.
- Bloquear o endereço IP de origem no Firewall se identificado.
- Auditar logs de acesso das últimas 72 horas nos sistemas afetados.
- Verificar se outras contas foram acessadas a partir do mesmo vetor.
- Comunicar o usuário legítimo da conta e solicitar troca de senha em todos os serviços.

## credential_compromise
- Forçar redefinição de senha imediata para a conta comprometida.
- Revogar todos os tokens de sessão ativos da conta.
- Verificar tentativas de acesso a outros sistemas com as mesmas credenciais.
- Ativar autenticação em dois fatores se ainda não ativo.
- Auditar ações realizadas com a conta no período de comprometimento.

## suspicious_activity
- Registrar e preservar evidências (capturas de tela, logs, e-mails).
- Monitorar o ativo suspeito por 24h antes de tomar ações disruptivas.
- Comunicar o responsável técnico do sistema afetado para análise.
- Evitar alertar o possível atacante com ações visíveis prematuras.
- Escalar para ETIR caso a atividade suspeita se confirme ou escale.

## denial_of_service
- Identificar a origem do tráfego anômalo nos logs do Firewall.
- Aplicar regras de rate limiting e bloqueio de IPs de origem no Firewall.
- Ativar proteções de mitigação DDoS disponíveis na infraestrutura.
- Comunicar usuários afetados com previsão de normalização.
- Registrar volume, duração e vetores para relatório pós-incidente.

## other
- Documentar detalhadamente o incidente antes de qualquer ação.
- Acionar o responsável técnico do sistema ou ativo afetado.
- Escalar para ETIR se houver dúvida sobre gravidade ou escopo.
- Preservar logs e evidências durante toda a investigação.
- Seguir o Plano de Gestão de Incidentes de SI institucional.
