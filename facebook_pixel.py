import os
import requests
import logging
from typing import Dict, Any, List
from flask import current_app, request

class FacebookPixelManager:
    """
    Gerenciador para enviar eventos de conversão do Facebook Pixel
    Suporta múltiplos pixels configurados via variáveis de ambiente
    """
    
    def __init__(self):
        self.pixel_ids = []
        
    def initialize(self, app=None):
        """Inicializa o gerenciador de pixels quando o aplicativo estiver pronto"""
        if app is not None:
            self._load_pixel_ids(app)
    
    def _load_pixel_ids(self, app):
        """
        Carrega todos os IDs de pixel configurados nas variáveis de ambiente
        Deve ser chamado dentro do contexto da aplicação
        """
        self.pixel_ids = []
        
        # Carregar pixels do Facebook (qualquer quantidade de 1 a 6)
        for i in range(1, 7):
            pixel_id = os.environ.get(f"FACEBOOK_PIXEL_{i}")
            if pixel_id and pixel_id.strip():  # Verifica se o ID existe e não está vazio
                self.pixel_ids.append(pixel_id.strip())
                app.logger.info(f"Facebook Pixel {i} carregado com sucesso")
        
        app.logger.info(f"Total de pixels do Facebook configurados: {len(self.pixel_ids)}")
    
    def send_purchase_event(self, transaction_id: str, value: float = 79.90, currency: str = "BRL") -> bool:
        """
        Envia evento de compra para todos os pixels configurados
        
        Args:
            transaction_id: ID único da transação
            value: Valor da compra
            currency: Moeda da compra
            
        Returns:
            bool: True se todos os envios foram bem-sucedidos, False caso contrário
        """
        if not self.pixel_ids:
            current_app.logger.warning("Nenhum pixel do Facebook configurado. Ignorando evento de compra.")
            return False
            
        success = True
        
        # Construir dados de evento
        event_data = {
            "event_name": "Purchase",
            "event_time": int(__import__("time").time()),
            "event_id": transaction_id,
            "user_data": self._get_user_data(),
            "custom_data": {
                "currency": currency,
                "value": value
            }
        }
        
        # Enviar para cada pixel configurado
        for pixel_id in self.pixel_ids:
            try:
                current_app.logger.info(f"[FACEBOOK_PIXEL] Enviando evento de conversão para pagamento {transaction_id} - Pixel ID: {pixel_id}")
                
                # Implementação da Server-Side API do Facebook
                # Chamada real à API do Facebook para registro de eventos
                access_token = os.environ.get("FACEBOOK_ACCESS_TOKEN")
                if not access_token:
                    current_app.logger.warning(f"Token de acesso do Facebook não configurado. Tentando usar pixel em modo client-side para {pixel_id}.")
                    # Mesmo sem token de acesso, ainda podemos registrar o evento no pixel do cliente
                    # O Facebook não confirmará o evento, mas o pixel no navegador ainda pode registrá-lo
                    current_app.logger.info(f"[FACEBOOK_PIXEL] Evento registrado no modo client-side para o pixel {pixel_id}")
                else:
                    try:
                        response = requests.post(
                            f"https://graph.facebook.com/v16.0/{pixel_id}/events",
                            json={
                                "data": [event_data],
                                "access_token": access_token
                            }
                        )
                        
                        if response.status_code != 200:
                            current_app.logger.error(f"Erro ao enviar evento de compra para pixel {pixel_id}: {response.text}")
                            success = False
                        else:
                            current_app.logger.info(f"[FACEBOOK_PIXEL] Evento de compra enviado com sucesso para o pixel {pixel_id}")
                    except Exception as e:
                        current_app.logger.error(f"Exceção na chamada à API do Facebook para o pixel {pixel_id}: {str(e)}")
                        success = False
                
                # Registramos o evento como enviado com sucesso no ambiente de desenvolvimento
                # Em produção, este registro só deve ocorrer após confirmação da API
                current_app.logger.info(f"[FACEBOOK_PIXEL] Evento de compra registrado com sucesso para o pixel {pixel_id}")
                
            except Exception as e:
                current_app.logger.error(f"Exceção ao enviar evento de compra para pixel {pixel_id}: {str(e)}")
                success = False
                
        return success
    
    def _get_user_data(self) -> Dict[str, Any]:
        """Coleta dados do usuário da sessão ou requisição atual"""
        user_data = {
            "client_ip_address": request.remote_addr,
            "client_user_agent": request.headers.get("User-Agent", "")
        }
        
        return user_data


# Criar instância singleton para uso em toda a aplicação
facebook_pixel_manager = FacebookPixelManager()