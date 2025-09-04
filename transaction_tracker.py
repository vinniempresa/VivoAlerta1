import time
from typing import Dict, Any, Tuple
from flask import request

# Armazenamento em memória para controle de tentativas de transação
IP_TRANSACTION_ATTEMPTS = {}
IP_BANS = {}
MAX_ATTEMPTS_PER_IP = 10  # Máximo de tentativas por IP sem transação bem-sucedida
BAN_DURATION = 86400  # 24 horas em segundos

def get_client_ip() -> str:
    """Obtém o IP do cliente da requisição atual"""
    if request.headers.get('X-Forwarded-For'):
        # Se estiver atrás de um proxy, pegar o primeiro IP da lista
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        return request.remote_addr or '0.0.0.0'

def is_transaction_ip_banned(ip: str) -> bool:
    """Verifica se um IP está banido temporariamente"""
    if ip in IP_BANS:
        ban_time = IP_BANS[ip]
        if time.time() < ban_time:
            # IP ainda está banido
            return True
        else:
            # Tempo de ban expirou
            del IP_BANS[ip]
    return False

def track_transaction_attempt(ip: str, data: Dict[str, Any], transaction_id: str = None) -> Tuple[bool, str]:
    """
    Rastreia tentativas de transação por IP para evitar abuso
    Retorna (permitido, mensagem)
    """
    now = time.time()
    
    # Se uma transação foi concluída com sucesso, resetar o contador
    if transaction_id:
        if ip in IP_TRANSACTION_ATTEMPTS:
            del IP_TRANSACTION_ATTEMPTS[ip]
        return True, f"Transação {transaction_id} registrada com sucesso"
    
    # Verifica se o IP está banido
    if is_transaction_ip_banned(ip):
        return False, "Excesso de tentativas de transação detectado. Tente novamente em 24 horas."
    
    # Inicializa ou atualiza o contador de tentativas
    if ip not in IP_TRANSACTION_ATTEMPTS:
        IP_TRANSACTION_ATTEMPTS[ip] = {
            'attempts': 1,
            'first_attempt': now,
            'last_attempt': now
        }
    else:
        IP_TRANSACTION_ATTEMPTS[ip]['attempts'] += 1
        IP_TRANSACTION_ATTEMPTS[ip]['last_attempt'] = now
        
        # Verifica se excedeu o limite de tentativas
        if IP_TRANSACTION_ATTEMPTS[ip]['attempts'] > MAX_ATTEMPTS_PER_IP:
            # Banir o IP por 24 horas
            IP_BANS[ip] = now + BAN_DURATION
            del IP_TRANSACTION_ATTEMPTS[ip]
            return False, "Excesso de tentativas de transação detectado. Tente novamente em 24 horas."
    
    return True, f"Tentativa {IP_TRANSACTION_ATTEMPTS[ip]['attempts']} registrada"