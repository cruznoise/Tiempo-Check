from app.extensions import db
from datetime import datetime
from sqlalchemy import Index

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    # Campos existentes
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    
    # ========================================================================
    # PERFIL MANUAL (del formulario de registro)
    # ========================================================================
    dedicacion = db.Column(db.String(50))  # estudiante, trabajador, freelancer, etc.
    horario_preferido = db.Column(db.String(50))  # manana, tarde, noche, flexible
    dias_trabajo = db.Column(db.String(50))  # lun_vie, lun_sab, toda_semana, finde_semana
    
    # ========================================================================
    # PERFIL INFERIDO AUTOMÁTICAMENTE (ML)
    # ========================================================================
    tipo_inferido = db.Column(db.String(50))  # estudiante, trabajador, mixto
    confianza_inferencia = db.Column(db.Float, default=0.0)  # 0.0 - 1.0
    
    # Patrones detectados automáticamente
    hora_pico_inicio = db.Column(db.Integer)  # 0-23
    hora_pico_fin = db.Column(db.Integer)  # 0-23
    dias_activos_patron = db.Column(db.String(50))  # "0,1,2,3,4" = lun-vie
    
    # Metadata
    perfil_actualizado_en = db.Column(db.DateTime)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hashea y guarda la contraseña"""
        from werkzeug.security import generate_password_hash
        self.contrasena = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.contrasena, password)
    
    def to_dict(self):
        """Convierte el perfil a diccionario para API"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'correo': self.correo,
            'dedicacion': self.dedicacion,
            'horario_preferido': self.horario_preferido,
            'dias_trabajo': self.dias_trabajo,            
            'tipo_inferido': self.tipo_inferido,
            'confianza_inferencia': self.confianza_inferencia,
            'hora_pico_inicio': self.hora_pico_inicio,
            'hora_pico_fin': self.hora_pico_fin,
            'dias_activos_patron': self.dias_activos_patron,           
            'perfil_actualizado_en': self.perfil_actualizado_en.isoformat() if self.perfil_actualizado_en else None,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }
class Registro(db.Model):
    __tablename__ = 'registro'
    id = db.Column(db.Integer, primary_key=True)
    dominio = db.Column(db.String(255))
    tiempo = db.Column(db.Integer)
    fecha = db.Column(db.DateTime)
    fecha_hora = db.Column(db.DateTime)  
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column('Id', db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Restricción única compuesta
    __table_args__ = (
        db.UniqueConstraint('nombre', 'usuario_id', name='unique_categoria_usuario'),
    )
    #fecha_hora = db.Column(db.DateTime, nullable=True, index=True)

class DominioCategoria(db.Model):
    __tablename__ = 'dominio_categoria'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dominio = db.Column(db.String(255), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'))
    categoria = db.Column(db.String(120), nullable=False, default='Sin categoría')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False) 
    # Relaciones
    categoria_obj = db.relationship('Categoria', backref='dominios')
    usuario = db.relationship('Usuario', backref='dominios_categorizados')
    __table_args__ = (
        db.UniqueConstraint('dominio', 'usuario_id', name='uq_dominio_usuario'),
    )

class MetaCategoria(db.Model):
    __tablename__ = 'metas_categoria'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'), nullable=False)
    minutos_meta = db.Column(db.Integer, nullable=False) 
    origen = db.Column(db.Enum('manual', 'coach', 'sistema'), default='manual', nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow) 
    cumplida = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')

class LimiteCategoria(db.Model):
    __tablename__ = 'limite_categoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'), nullable=False)
    limite_minutos = db.Column(db.Integer, nullable=False)

    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')

class UsuarioLogro(db.Model):
    __tablename__ = 'usuario_logro'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    logro_id = db.Column(db.Integer, nullable=False)

    usuario = db.relationship('Usuario')

    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "logro_id": self.logro_id
        }


class FeaturesCategoriaDiaria(db.Model):
    __tablename__ = "features_categoria_diaria"

    usuario_id = db.Column(db.Integer, nullable=False, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False, primary_key=True)

    minutos = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_fcdiaria_usuario_fecha", "usuario_id", "fecha"),
        Index("ix_fcdiaria_fecha", "fecha"),
        Index("ix_fcdiaria_usuario_categoria", "usuario_id", "categoria"),
    )

    def __repr__(self):
        return f"<FCD {self.usuario_id} {self.fecha} {self.categoria}={self.minutos}>"
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class AggVentanaCategoria(db.Model):
    __tablename__ = 'agg_ventana_categoria'
    usuario_id = db.Column(db.Integer, primary_key=True)
    categoria  = db.Column(db.String(64), primary_key=True)
    ventana    = db.Column(db.String(8),  primary_key=True)  # '7d','14d','30d'
    fecha_fin  = db.Column(db.Date,       primary_key=True)
    minutos_sum      = db.Column(db.Float, nullable=False)
    minutos_promedio = db.Column(db.Float, nullable=False)
    dias_con_datos   = db.Column(db.Integer, nullable=False)
    pct_del_total    = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class AggEstadoDia(db.Model):
    __tablename__ = 'agg_estado_dia'
    usuario_id = db.Column(db.Integer, primary_key=True)
    fecha      = db.Column(db.Date,    primary_key=True)
    categoria  = db.Column(db.String(64), primary_key=True)
    minutos    = db.Column(db.Float, nullable=False)
    meta_min   = db.Column(db.Float)
    limite_min = db.Column(db.Float)
    cumplio_meta   = db.Column(db.Boolean, default=False)
    excedio_limite = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class AggKpiRango(db.Model):
    __tablename__ = 'agg_kpi_rango'
    usuario_id = db.Column(db.Integer, primary_key=True)
    rango      = db.Column(db.String(12), primary_key=True)  # 'hoy','7dias','mes','total'
    fecha_ref  = db.Column(db.Date, primary_key=True)
    min_total         = db.Column(db.Float, nullable=False)
    min_productivo    = db.Column(db.Float, nullable=False)
    min_no_productivo = db.Column(db.Float, nullable=False)
    pct_productivo    = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class ContextoDia(db.Model):
    """Contexto de días atípicos detectados"""
    __tablename__ = 'contexto_dia'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    es_atipico = db.Column(db.Boolean, default=False)
    motivo = db.Column(db.String(100))
    motivo_detalle = db.Column(db.Text)
    uso_esperado_min = db.Column(db.Float)
    uso_real_min = db.Column(db.Float)
    desviacion_pct = db.Column(db.Float)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    usuario = db.relationship('Usuario', backref='contextos_dia')
    
    def __repr__(self):
        return f'<ContextoDia {self.fecha} U{self.usuario_id} atipico={self.es_atipico}>'

class PatronCategoria(db.Model):
    __tablename__ = 'patrones_categoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    patron = db.Column(db.String(512), nullable=False, unique=True)  # ← varchar(512) y UNIQUE
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)  
    creado_en = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    actualizado_en = db.Column(
        db.DateTime, 
        nullable=False, 
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')
    
    def __repr__(self):
        return f'<PatronCategoria {self.patron} -> Cat{self.categoria_id}>'
    
class RachaUsuario(db.Model):
    __tablename__ = 'rachas_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'), nullable=True)  # NULL = racha general
    tipo_racha = db.Column(db.Enum('metas', 'limites', 'uso_diario'), default='metas')
    racha_actual = db.Column(db.Integer, default=0)
    racha_maxima = db.Column(db.Integer, default=0)
    ultima_fecha = db.Column(db.Date)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuario = db.relationship('Usuario')
    categoria = db.relationship('Categoria')
    
    def __repr__(self):
        return f'<RachaUsuario U{self.usuario_id} actual={self.racha_actual} max={self.racha_maxima}>'
    

class ConfiguracionLogro(db.Model):
    """Configuración de condiciones para desbloquear logros dinámicamente"""
    __tablename__ = 'logros_dinamicos'
    
    logro_id = db.Column(db.Integer, primary_key=True)
    tipo_condicion = db.Column(db.String(50))  # 'racha_dias', 'tiempo_categoria', 'meta_cumplida', etc.
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.Id'), nullable=True)
    valor_referencia = db.Column(db.Integer)  # Valor que se debe alcanzar para desbloquear
    
    categoria = db.relationship('Categoria')
    
    def __repr__(self):
        return f'<ConfiguracionLogro {self.logro_id} {self.tipo_condicion}={self.valor_referencia}>'
    

class SesionFocus(db.Model):
    __tablename__ = 'sesiones_focus'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fin_programado = db.Column(db.DateTime, nullable=False)
    fin_real = db.Column(db.DateTime)
    duracion_minutos = db.Column(db.Integer, nullable=False)
    tiempo_real_minutos = db.Column(db.Integer)
    completada = db.Column(db.Boolean, default=False)
    modo_estricto = db.Column(db.Boolean, default=False)
    categorias_bloqueadas = db.Column(db.Text) 
    usuario = db.relationship('Usuario', backref='sesiones_focus')
    intentos_bloqueo = db.relationship('IntentoBloqeuoFocus', backref='sesion', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'inicio': self.inicio.isoformat() if self.inicio else None,
            'fin_programado': self.fin_programado.isoformat() if self.fin_programado else None,
            'fin_real': self.fin_real.isoformat() if self.fin_real else None,
            'duracion_minutos': self.duracion_minutos,
            'tiempo_real_minutos': self.tiempo_real_minutos,
            'completada': self.completada,
            'modo_estricto': self.modo_estricto,
            'categorias_bloqueadas': self.categorias_bloqueadas
        }


class IntentoBloqeuoFocus(db.Model):
    __tablename__ = 'intentos_bloqueo_focus'
    
    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(db.Integer, db.ForeignKey('sesiones_focus.id'), nullable=False)
    momento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    url_bloqueada = db.Column(db.String(500))
    categoria = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'sesion_id': self.sesion_id,
            'momento': self.momento.isoformat() if self.momento else None,
            'url_bloqueada': self.url_bloqueada,
            'categoria': self.categoria
        }