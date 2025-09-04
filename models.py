from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class RecoveryData(db.Model):
    """
    Modelo para armazenar dados de recuperação de vendas via SMS
    """
    __tablename__ = 'recovery_data'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(20), unique=True, nullable=False, index=True)
    transaction_id = db.Column(db.String(100), nullable=False)
    
    # Dados do usuário
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(11), nullable=False)
    cidade = db.Column(db.String(50), nullable=False, default='São Paulo')
    
    # Dados do pagamento
    pix_code = db.Column(db.Text, nullable=True)  # Código PIX copia e cola
    pix_qr_code = db.Column(db.Text, nullable=True)  # URL do QR Code
    valor = db.Column(db.Float, nullable=False, default=59.90)
    
    # URLs e tracking
    recovery_url = db.Column(db.String(200), nullable=False)
    sms_sent = db.Column(db.Boolean, default=False)
    sms_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Controle de acesso
    accessed_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RecoveryData {self.slug}: {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'slug': self.slug,
            'transaction_id': self.transaction_id,
            'nome': self.nome,
            'telefone': self.telefone,
            'cpf': self.cpf,
            'cidade': self.cidade,
            'pix_code': self.pix_code,
            'pix_qr_code': self.pix_qr_code,
            'valor': self.valor,
            'recovery_url': self.recovery_url,
            'sms_sent': self.sms_sent,
            'sms_sent_at': self.sms_sent_at.isoformat() if self.sms_sent_at else None,
            'accessed_count': self.accessed_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_by_slug(cls, slug):
        """Recupera dados por slug"""
        return cls.query.filter_by(slug=slug).first()
    
    @classmethod
    def create_recovery_record(cls, slug, transaction_id, user_data, pix_data, recovery_url):
        """Cria um novo registro de recuperação"""
        recovery = cls(
            slug=slug,
            transaction_id=transaction_id,
            nome=user_data.get('name') or user_data.get('nome', 'Cliente'),
            telefone=user_data.get('phone') or user_data.get('telefone', ''),
            cpf=user_data.get('cpf', ''),
            cidade=user_data.get('cidade', 'São Paulo'),
            pix_code=pix_data.get('pixCode', ''),
            pix_qr_code=pix_data.get('pixQrCode', ''),
            valor=pix_data.get('amount', 59.90),
            recovery_url=recovery_url,
            sms_sent=False
        )
        
        db.session.add(recovery)
        db.session.commit()
        return recovery
    
    def mark_sms_sent(self):
        """Marca SMS como enviado"""
        self.sms_sent = True
        self.sms_sent_at = datetime.utcnow()
        db.session.commit()
    
    def mark_accessed(self):
        """Marca como acessado"""
        self.accessed_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()