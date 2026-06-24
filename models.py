from sqlalchemy import Column, Integer, String, Float
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