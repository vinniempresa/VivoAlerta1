import requests
import json

# Testar a API de SMS diretamente
url = 'https://api-sms.replit.app/api/v1/sms/send'
headers = {
    'Authorization': 'Bearer sms__b8o-sVVAyPAnYj9tvAZ92GwQQ0LpyTq',
    'Content-Type': 'application/json'
}
data = {
    'phoneNumber': '61999114966',
    'message': 'Teste direto da API SMS - Vivo',
    'priority': 5
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')
    print(f'Headers: {dict(response.headers)}')
except Exception as e:
    print(f'Erro na requisição: {str(e)}')