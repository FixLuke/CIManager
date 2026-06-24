# Gestionale Magazzino Locale (CIManager)

Ssoftware Gestionale pronto all'uso con backend in Python (FastAPI) e frontend (HTML5/Tailwind), Progettato per funzionare in modo sicuro con HTTPS all'interno di una rete locale, anche senza connessione internet, quindi il sistema girerà tutto su server locale, e potrà essere poi utilizzato dagli host della rete (con il relativo certificato generato), l'utilizzo è pensato per praticità con uno smartphone.

---

## Prerequisiti del sistema

Prima di configurare il progetto sul nuovo computer, assicurati di avere installato:
- **Python 3.10+**
- **Git**
- **mkcert** (Per la gestione dei certificati SSL locali)

---

## Guida alla configurazione (Nuovo PC)

Segui questi passaggi per clonare il progetto e rimettere in piedi l'intero ambiente di lavoro in pochi minuti.

### 1. Clonare il Progetto da GitHub
Apri il terminale del nuovo computer nella cartella in cui vuoi salvare il software e digita:
```bash
git clone [https://github.com/FixLuke/CIManager.git](https://github.com/FixLuke/CIManager.git)
cd CIManager
```

### 2. Creare e Attivare l'ambiente Virtuale (VENV)
Per evitare conflitti con le libreri attualmente installate sul sistema, crea un ambiente isolato Python:

#### Windows (Powershell)
```
python -m venv venv
.\venv\Scripts\activate
```

#### Linux
```
python -m venv venv
source venv/bin/activate
```

(L'ambiente venv sarà attivo quando vedrai la scritta in verde "venv" da terminale)


### 3. Installare le dipendenze di sistema

Con il venv attivo, lanciamo il comando per installare automaticamente FastAPI,Uvicorn, SQLAlchemy...Questo Leggendo il file requirements.txt
```
pip install -r requirements.txt
```

### 4. Rigenerare i certificati HTTPS locali

I certificati "*.pem"  sono bloccati da  per motivi di sicurezza, quindi vanno ricreati sui nuovi dispositivi:

1) Se è la prima volta che si usa mkcert
    ```
    mkcert -install
    ```
2) Trovare l'IP locale del dispositivo sul quale stiamo avviando il software (es. 192.168.1.56)

3) Genera i certificati aggiornati inserendo localhost e l'IP del dispositivo appena trovato (esegui il comando dentro la cartella del progetto)

    ```
    mkcert localhost 127.0.0.1 L_IP_LOCALE_DEL_NUOVO_PC
    ```
    (il seguente comando genera 2 file .pem direttamente nella directory corrente)


## Come Avviare il Gestionale

1) Aprire il terminale nella cartella di progetto

2) Assicurarsi che si è in venv (scritta in verde)

3)Avviare il server con 
    ```
    uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile "./localhost+2-key.pem" --ssl-certfile "./localhost+2.pem" --reload
     ```
4) Per accedere dal PC stesso che ospita il server, andare su rowser e digitare 

    ```
    https://localhost:8000
    ```
4B) Da smartphone/Tablet

    Accedere alla stessa rete dove è ospitato il server e digitare:

    ```
    https://L_IP_LOCALE_DEL_NUOVO_PC:8000
    ```

## Sincronizzare i nuovi SMartphone (una tantum dato che il certificato dovrebbe durare anni)

1) digita il comando "mkcert -CAROOT" per trovare il percorso nel quale risiede il file generato

2) copia il file "rootCA.pem" e invialo allo smartphone

3) Per caricarlo su smartphone: 

**Su Android:** Vai in Impostazioni > Sicurezza > Altre impostazioni > Installa da memoria e seleziona Certificato CA.

**Su iOS:** Scarica il file da Safari, installalo dalla voce Profilo scaricato in alto nelle Impostazioni, poi vai su Generali > Info > Attendibilità certificati e abilita l'interruttore di piena fiducia per il profilo mkcert.

----------------


PER INVECE AVVIARE IL SERVER SU QUESTA STESSA MACCHINA E VEDERLO QUI (MAGARI PER TESTARLO):
uvicorn main:app --reload