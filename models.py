from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    client_id = Column(Integer, primary_key=True)
    client_name = Column(String(100), nullable=False)
    uploads = relationship("Upload", back_populates="client")

class Upload(Base):
    __tablename__ = 'uploads'
    upload_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'))
    upload_date = Column(DateTime, default=datetime.utcnow)
    source_file = Column(String(255))
    
    client = relationship("Client", back_populates="uploads")
    signal_results = relationship("SignalResult", back_populates="upload")
    index_results = relationship("IndexResult", back_populates="upload")
    pattern_results = relationship("PatternResult", back_populates="upload")
    alerts = relationship("Alert", back_populates="upload")

class Signal(Base):
    __tablename__ = 'signals'
    signal_id = Column(String(50), primary_key=True)
    signal_name = Column(String(100))
    domain = Column(String(50))
    layer = Column(Integer)

class SignalResult(Base):
    __tablename__ = 'signal_results'
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey('uploads.upload_id'))
    signal_id = Column(String(50), ForeignKey('signals.signal_id'))
    raw_value = Column(Float)
    normalized_score = Column(Float)
    trend = Column(Float)
    confidence = Column(Float)
    
    upload = relationship("Upload", back_populates="signal_results")

class IndexResult(Base):
    __tablename__ = 'index_results'
    upload_id = Column(Integer, ForeignKey('uploads.upload_id'), primary_key=True)
    ssi = Column(Float)
    fi = Column(Float)
    ri = Column(Float)
    qci = Column(Float)
    bei = Column(Float)
    quality_maturity_score = Column(Float)
    
    upload = relationship("Upload", back_populates="index_results")

class PatternResult(Base):
    __tablename__ = 'pattern_results'
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey('uploads.upload_id'))
    pattern_id = Column(String(50))
    active = Column(Boolean)
    strength = Column(Float)
    interpretation = Column(Text)
    
    upload = relationship("Upload", back_populates="pattern_results")

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey('uploads.upload_id'))
    alert_type = Column(String(50))
    severity = Column(String(20))
    message = Column(Text)
    
    upload = relationship("Upload", back_populates="alerts")

def seed_signals(session):
    signals = [
        Signal(signal_id="S001", signal_name="Adverse Events", domain="SSI", layer=1),
        Signal(signal_id="S002", signal_name="Deviation Rate", domain="FI", layer=1),
        Signal(signal_id="S003", signal_name="Audit Findings", domain="RI", layer=2),
        Signal(signal_id="S004", signal_name="Batch Reject Rate", domain="QCI", layer=1),
        Signal(signal_id="S005", signal_name="Training Compliance", domain="BEI", layer=1),
        Signal(signal_id="S006", signal_name="Customer Complaints", domain="SSI", layer=1),
        Signal(signal_id="S007", signal_name="EM Excursions", domain="FI", layer=1),
        Signal(signal_id="S008", signal_name="CAPA Overdue", domain="RI", layer=1)
    ]
    for s in signals:
        if not session.query(Signal).filter_by(signal_id=s.signal_id).first():
            session.add(s)
    session.commit()

def init_db(engine_url="sqlite:///vqp_prototype.db"):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(engine_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_signals(session)
    session.close()
    
    return engine
