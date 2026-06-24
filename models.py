from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Prodotto(Base):
    __tablename__ = "prodotti"

    # Il codice a barre diventa la chiave primaria (ID univoco)
    codice_a_barre = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    quantita = Column(Integer, default=0)
    
    # Prezzi
    prezzo_acquisto = Column(Float, nullable=False)
    prezzo_pubblico = Column(Float, nullable=False)
    
    # Immagine
    foto_path = Column(String, nullable=True)

class Vendita(Base):
    __tablename__ = "vendite"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ora = Column(DateTime, default=datetime.now)
    totale = Column(Float)
    
    dettagli = relationship("DettaglioVendita", back_populates="vendita")

class DettaglioVendita(Base):
    __tablename__ = "dettagli_vendita"
    
    id = Column(Integer, primary_key=True, index=True)
    vendita_id = Column(Integer, ForeignKey("vendite.id"))
    codice_a_barre = Column(String)
    nome_prodotto = Column(String)  # Salviamo il nome nel caso in futuro cancelli il prodotto dal magazzino!
    quantita = Column(Integer)
    prezzo_unitario = Column(Float) # Salviamo il prezzo al momento della vendita
    
    vendita = relationship("Vendita", back_populates="dettagli")