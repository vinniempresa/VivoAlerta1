import os
import requests
from datetime import datetime
from flask import current_app, request
from typing import Dict, Any, Optional
import random
import string
import time
from transaction_tracker import track_transaction_attempt, get_client_ip, is_transaction_ip_banned

class For4Payments2API:
    API_URL = "https://app.for4payments.com.br/api/v1"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.extra_headers = {}  # Headers adicionais para evitar problemas de 403 Forbidden

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'Authorization': self.secret_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Adicionar headers extras (para evitar 403 Forbidden)
        if self.extra_headers:
            headers.update(self.extra_headers)
            current_app.logger.debug(f"Usando headers personalizados: {headers}")

        return headers

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

    def create_fixed_transaction_payment(self) -> Dict[str, Any]:
        """
        Cria uma transação PIX fixa com os mesmos dados do cliente e valor de R$79,90
        """
        try:
            # Lista de primeiros nomes brasileiros
            first_names = [
                "Ana", "Maria", "João", "José", "Carlos", "Paulo", "Pedro", "Francisco", 
                "Luiz", "Marcos", "Daniel", "Rafael", "Bruno", "Diego", "Felipe",
                "Gustavo", "Lucas", "Mateus", "Gabriel", "Leonardo", "Rodrigo",
                "Juliana", "Fernanda", "Amanda", "Letícia", "Camila", "Priscila",
                "Patricia", "Sandra", "Mônica", "Débora", "Carla", "Mariana",
                "Larissa", "Vanessa", "Adriana", "Claudia", "Roberta", "Cristina",
                "Ricardo", "André", "Fabio", "Marcelo", "Alexandre", "Sergio",
                "Roberto", "Antonio", "Renato", "Thiago", "Vinicius", "Fernando",
                "Henrique", "Leandro", "Caio", "Igor", "Eduardo", "Danilo",
                "Beatriz", "Isabela", "Carolina", "Natália", "Bruna", "Bianca",
                "Raquel", "Tatiana", "Simone", "Eliane", "Luciana", "Regina"
            ]
            
            # Lista de sobrenomes brasileiros
            last_names = [
                "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
                "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins",
                "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira",
                "Barbosa", "Rocha", "Dias", "Monteiro", "Cardoso", "Reis", "Araújo",
                "Correia", "Castro", "Andrade", "Nascimento", "Moreira", "Mendes",
                "Freitas", "Ramos", "Morais", "Campos", "Cavalcanti", "Nunes",
                "Teixeira", "Melo", "Barros", "Pinto", "Marques", "Nogueira",
                "Miranda", "Duarte", "Macedo", "Farias", "Brito", "Cardoso",
                "Azevedo", "Moura", "Franco", "Pires", "Cunha", "Guimarães",
                "Coelho", "Santana", "Machado", "Borges", "Sales", "Matos"
            ]
            
            # Gerar nome aleatório
            random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Dados com nome variável, mas outros dados fixos
            user_data = {
                "name": random_name,
                "email": "compradecurso@gmail.com",
                "cpf": "83054235149",
                "phone": "11998346572",
                "amount": 79.90,
                "description": "Curso Completo com Certificado"
            }
            
            current_app.logger.info(f"Transação criada para: {random_name}")
            
            # Dados fixos conforme solicitado
            # user_data = {
            #     "name": "Marina Souza",
            #     "email": "compradecurso@gmail.com",
            #     "cpf": "83054235149",
            #     "phone": "11998346572",
            #     "amount": 79.90,
            #     "description": "Curso Completo com Certificado"
            # }
            
            # Calcular o valor em centavos
            amount_in_cents = int(float(user_data['amount']) * 100)
            current_app.logger.info(f"Valor do pagamento: R$ {float(user_data['amount']):.2f} ({amount_in_cents} centavos)")

            # Preparação dos dados para a API no formato correto
            payment_data = {
                "name": user_data["name"],
                "email": user_data["email"],
                "cpf": user_data["cpf"],
                "phone": user_data["phone"],
                "paymentMethod": "PIX",
                "amount": amount_in_cents,
                "items": [{
                    "title": "Curso Completo com Certificado",
                    "quantity": 1,
                    "unitPrice": amount_in_cents,
                    "tangible": False
                }]
            }

            current_app.logger.info(f"Dados para pagamento formatados: {payment_data}")

            try:
                # Chamar a API PIX diretamente
                headers = self._get_headers()

                # Log dos headers (ocultando a chave de autenticação)
                safe_headers = headers.copy()
                if 'Authorization' in safe_headers and len(safe_headers['Authorization']) > 6:
                    safe_headers['Authorization'] = f"{safe_headers['Authorization'][:3]}...{safe_headers['Authorization'][-3:]}"
                current_app.logger.info(f"Headers da requisição: {safe_headers}")
                current_app.logger.info(f"Endpoint API: {self.API_URL}/transaction.purchase")

                # Lista de user agents para variar os headers
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/94.0",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
                ]

                # Lista de idiomas para variar nos headers
                languages = [
                    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
                    "es-ES,es;q=0.9,pt;q=0.8,en;q=0.7"
                ]

                # Configurar headers extras aleatórios
                extra_headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept-Language": random.choice(languages),
                    "Cache-Control": random.choice(["max-age=0", "no-cache"]),
                    "X-Requested-With": "XMLHttpRequest",
                    "X-Cache-Buster": str(int(time.time() * 1000)),
                    "Referer": "https://portal.vivo-cadastro.com/transacao",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty"
                }

                # Combinar com headers base
                headers.update(extra_headers)

                response = requests.post(
                    f"{self.API_URL}/transaction.purchase",
                    json=payment_data,
                    headers=headers,
                    timeout=30
                )

                current_app.logger.info(f"Resposta recebida (Status: {response.status_code})")

                if response.status_code == 200:
                    response_data = response.json()
                    current_app.logger.info(f"Resposta da API: {response_data}")

                    return {
                        'id': response_data.get('id') or response_data.get('transactionId'),
                        'pixCode': response_data.get('pixCode') or response_data.get('pix', {}).get('code'),
                        'pixQrCode': response_data.get('pixQrCode') or response_data.get('pix', {}).get('qrCode'),
                        'expiresAt': response_data.get('expiresAt') or response_data.get('expiration'),
                        'status': response_data.get('status', 'pending')
                    }
                else:
                    error_message = f"Erro na API: {response.status_code} - {response.text}"
                    current_app.logger.error(error_message)
                    raise ValueError(error_message)
            except Exception as api_error:
                current_app.logger.error(f"Erro na chamada da API: {str(api_error)}")
                current_app.logger.warning("Usando PIX simulado em vez da API real")
                return self._generate_mock_pix_payment()

        except Exception as e:
            current_app.logger.error(f"Erro ao processar pagamento: {str(e)}")
            current_app.logger.warning("Usando PIX simulado em vez da API real")
            return self._generate_mock_pix_payment()

    def _generate_mock_pix_payment(self) -> Dict[str, Any]:
        """Gera um código PIX de simulação quando a API real falha ou está indisponível"""
        # Simulação de dados PIX para testes
        mock_pix_code = "00020126580014BR.GOV.BCB.PIX01362e07742c-5d0d-4c07-a32c-96f0e2952f4c5204000053039865802BR5925TREINAMENTO VIVO ONLINE6009SAO PAULO62070503***63047A12"
        mock_qr_code_url = "https://i.ibb.co/g9MVNR2/qrcode-pix-curso.png"

        current_app.logger.warning("Usando PIX simulado em vez da API real")

        return {
            "id": f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}",
            "status": "PENDING",
            "createdAt": datetime.now().isoformat(),
            "expiresAt": datetime.now().isoformat(),
            "pixCode": mock_pix_code,
            "pixQrCode": mock_qr_code_url,
            "amount": 79.90
        }

def create_payment2_api(secret_key: Optional[str] = None) -> For4Payments2API:
    """Factory function to create For4Payments2API instance"""
    # Usar a chave de API do ambiente ou a chave fornecida
    api_key = secret_key or os.environ.get('FOR4PAYMENTS_SECRET_KEY', 'ca46d320-d0f6-4387-9de4-2c9a91861725')
    
    return For4Payments2API(api_key)