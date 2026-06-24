from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel # <-- NUOVO
from typing import List        # <-- NUOVO
import database
import models
import os
import shutil
import uuid

class VoceCarrello(BaseModel):
    codice_a_barre: str
    quantita: int

os.makedirs("static/uploads", exist_ok=True)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def pagina_principale():
    return FileResponse("index.html")

# Endpoint per cercare un singolo prodotto tramite codice a barre
@app.get("/api/prodotti/{codice}")
def get_singolo_prodotto(codice: str, db: Session = Depends(get_db)):
    prodotto = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == codice).first()
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return prodotto

# CREATE / UPDATE (Upsert) Aggiunta o aggiornamento quantià di un prodotto già a magazzino
@app.post("/api/prodotti")
async def aggiungi_prodotto(
    codice_a_barre: str = Form(...),
    nome: str = Form(...),
    quantita: int = Form(...),
    prezzo_acquisto: float = Form(...),
    prezzo_pubblico: float = Form(...),
    foto: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    esistente = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == codice_a_barre).first()
    
    # SE ESISTE GIA': Aggiorniamo solo la quantità
    if esistente:
        esistente.quantita += quantita
        # Se i prezzi sono cambiati, li aggiorniamo (opzionale, ma utile)
        esistente.prezzo_acquisto = prezzo_acquisto
        esistente.prezzo_pubblico = prezzo_pubblico
        db.commit()
        db.refresh(esistente)
        return esistente

    # SE E' NUOVO: Procediamo con la creazione e il salvataggio della foto
    percorso_db = ""
    if foto and foto.filename:
        estensione = foto.filename.split(".")[-1]
        nome_file_univoco = f"{uuid.uuid4()}.{estensione}"
        percorso_fisico = f"static/uploads/{nome_file_univoco}"
        
        with open(percorso_fisico, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        percorso_db = f"/{percorso_fisico}" 

    nuovo_prodotto = models.Prodotto(
        codice_a_barre=codice_a_barre,
        nome=nome,
        quantita=quantita,
        prezzo_acquisto=prezzo_acquisto,
        prezzo_pubblico=prezzo_pubblico,
        foto_path=percorso_db
    )
    
    db.add(nuovo_prodotto)
    db.commit()
    db.refresh(nuovo_prodotto)
    return nuovo_prodotto

# READ
@app.get("/api/prodotti")
def lista_prodotti(db: Session = Depends(get_db)):
    return db.query(models.Prodotto).all()

# UPDATE QUANTITA
@app.put("/api/prodotti/{codice}/quantita")
def aggiorna_quantita(codice: str, variazione: int, db: Session = Depends(get_db)):
    prodotto = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == codice).first()
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    
    prodotto.quantita += variazione
    if prodotto.quantita < 0: 
        prodotto.quantita = 0 
    
    db.commit()
    return {"messaggio": "Quantità aggiornata"}

# DELETE
@app.delete("/api/prodotti/{codice}")
def elimina_prodotto(codice: str, db: Session = Depends(get_db)):
    prodotto = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == codice).first()
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    
    if prodotto.foto_path:
        percorso_fisico_foto = prodotto.foto_path.lstrip("/")
        if os.path.exists(percorso_fisico_foto):
            os.remove(percorso_fisico_foto)
            
    db.delete(prodotto)
    db.commit()
    return {"messaggio": "Prodotto eliminato"}

# Endpoint per concludere la vendita (scarico massivo)
@app.post("/api/vendita")
def concludi_vendita(voci: List[VoceCarrello], db: Session = Depends(get_db)):
    for voce in voci:
        prodotto = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == voce.codice_a_barre).first()
        if not prodotto:
            raise HTTPException(status_code=404, detail=f"Prodotto {voce.codice_a_barre} non trovato")
        if prodotto.quantita < voce.quantita:
            raise HTTPException(status_code=400, detail=f"Quantità insufficiente per {prodotto.nome}")
        
        # Sottrai la quantità venduta
        prodotto.quantita -= voce.quantita
        
    db.commit()
    return {"messaggio": "Vendita conclusa con successo"}