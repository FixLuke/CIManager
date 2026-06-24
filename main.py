from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel # <-- NUOVO
from typing import List        # <-- NUOVO
from datetime import datetime
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

from datetime import datetime

# Endpoint vendita:
@app.post("/api/vendita")
def concludi_vendita(voci: List[VoceCarrello], db: Session = Depends(get_db)):
    if not voci:
        raise HTTPException(status_code=400, detail="Carrello vuoto")
        
    totale_vendita = 0
    dettagli_da_salvare = []
    
    # 1. Controlla e scala il magazzino
    for voce in voci:
        prodotto = db.query(models.Prodotto).filter(models.Prodotto.codice_a_barre == voce.codice_a_barre).first()
        if not prodotto or prodotto.quantita < voce.quantita:
            raise HTTPException(status_code=400, detail=f"Errore scorte per {voce.codice_a_barre}")
        
        prodotto.quantita -= voce.quantita
        subtotale = prodotto.prezzo_pubblico * voce.quantita
        totale_vendita += subtotale
        
        # Prepara la riga dello scontrino
        dettagli_da_salvare.append(models.DettaglioVendita(
            codice_a_barre=prodotto.codice_a_barre,
            nome_prodotto=prodotto.nome,
            quantita=voce.quantita,
            prezzo_unitario=prodotto.prezzo_pubblico
        ))
        
    # 2. Crea lo scontrino principale
    nuova_vendita = models.Vendita(totale=totale_vendita, data_ora=datetime.now())
    db.add(nuova_vendita)
    db.commit()
    db.refresh(nuova_vendita)
    
    # 3. Collega le righe allo scontrino
    for d in dettagli_da_salvare:
        d.vendita_id = nuova_vendita.id
        db.add(d)
        
    db.commit()
    return {"messaggio": "Vendita conclusa", "id_vendita": nuova_vendita.id}

# Endpoint per leggere tutte le vendite passate
@app.get("/api/vendite")
def storico_vendite(db: Session = Depends(get_db)):
    # Restituisce le vendite in ordine cronologico inverso (le più recenti prima)
    return db.query(models.Vendita).order_by(models.Vendita.data_ora.desc()).all()

# Dettagli di un singolo scontrino:
@app.get("/api/vendite/{vendita_id}")
def dettagli_scontrino(vendita_id: int, db: Session = Depends(get_db)):
    vendita = db.query(models.Vendita).filter(models.Vendita.id == vendita_id).first()
    if not vendita:
        raise HTTPException(status_code=404, detail="Scontrino non trovato")
    
    # "Costruiamo" esplicitamente il pacchetto dati per assicurarci 
    # che FastAPI includa i dettagli della seconda tabella
    return {
        "id": vendita.id,
        "data_ora": vendita.data_ora,
        "totale": vendita.totale,
        "dettagli": [
            {
                "nome_prodotto": d.nome_prodotto,
                "quantita": d.quantita,
                "prezzo_unitario": d.prezzo_unitario
            } for d in vendita.dettagli
        ]
    }