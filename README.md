# electribe sampler — replica interattiva

Replica ispirata alla foto fornita. Il pannello è in `static/index.html` (HTML, CSS e JavaScript vanilla); WebSocket, clock, sequencer e sintesi audio sono in Python. Non è un'emulazione completa del firmware Korg. Il confronto puntuale con il manuale ufficiale e i limiti sono in [MANUALE_IMPLEMENTAZIONE.md](MANUALE_IMPLEMENTAZIONE.md).

Per tutti i comandi, i pattern, i WAV e la soluzione dei problemi audio, consulta la [guida completa](GUIDA.md).

## Prima prova

1. Estrai la ZIP e apri un terminale nella cartella `SimKorg-electribe-sampler-demo`.
2. Installa Python 3.11 o successivo, se non è già presente. Serve una connessione Internet solo per installare le dipendenze la prima volta.
3. Esegui i comandi per il tuo sistema operativo qui sotto.
4. Apri `http://127.0.0.1:8000/` nel browser. Lascia aperto il terminale mentre provi lo strumento; `Ctrl+C` ferma il server.

**macOS o Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

L'audio esce dal computer che esegue il server. Per ascoltarlo anche sul dispositivo che apre la pagina, tocca **Ascolta su questo dispositivo**. Aprendo direttamente `static/index.html` si vede il pannello, ma audio e sequencer richiedono il server. Se non senti nulla, controlla uscita audio, tasto Power e manopola Volume. Se il display segnala un errore audio, verifica che sia disponibile un dispositivo di uscita. Il microfono resta spento all'avvio: **Attiva microfono** apre l'ingresso del computer solo quando lo chiedi; **Input Level** ne regola il monitoraggio.

## Ascolto su iPad

1. Collega iPad e computer alla stessa rete Wi-Fi.
2. Sul computer avvia il server con `--host 0.0.0.0` invece di `--host 127.0.0.1`. Esempio macOS/Linux: `.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000`.
3. Trova l'indirizzo IP locale del computer e su Safari apri `http://INDIRIZZO-IP:8000/`.
4. Tocca **Ascolta su questo dispositivo**. Questo gesto è necessario per consentire a Safari di avviare l'audio. Tieni la pagina in primo piano mentre suoni.

Il computer può suonare insieme all'iPad; abbassa il suo volume se senti un doppio audio. Se Safari non si collega, controlla il firewall e che la rete Wi-Fi non isoli i dispositivi tra loro. Il flusso audio usa la rete locale e può avere un piccolo ritardo rispetto ai comandi.

## Uso

- Suona i 16 pad con mouse, tocco o tastiera: `1`–`8` e `Q W E R T Y U I`.
- I pulsanti **TRIGGER, SEQUENCER, KEYBOARD, CHORD, STEP JUMP** e **PATTERN SET** cambiano la funzione dei pad. I quattro pulsanti numerati selezionano l'ottava o il gruppo di pattern, secondo la modalità.
- **LPF, HPF e BPF** scelgono il filtro; **MFX SEND, AMP EG e IFX ON** attivano le rispettive funzioni audio della replica.
- Apri **Funzioni SimKorg** per importare WAV, scegliere pattern e usare i comandi aggiuntivi. La [guida completa](GUIDA.md) spiega ogni modalità e la registrazione.

La manopola `Input Level` regola il monitoraggio dell'ingresso audio del computer che esegue il server, quando il microfono è stato attivato esplicitamente e il dispositivo audio lo consente. Il pannello segue la foto `korg2.jpg`; le funzioni implementate sono una replica d'uso, non una copia del firmware Korg.

## Protocollo

`/ws` riceve eventi JSON `knob`, `pad`, `touch`, `button` e `value`; invia `state` con BPM, step, parte, modalità, LED, valori e due righe del display. `/audio` invia PCM stereo 16 bit/44,1 kHz al browser; l'interfaccia lo riproduce senza sintetizzarlo. `GET /api/samples` elenca i WAV; `POST /api/assign` associa un file a un pad; `POST /api/upload/{filename}?index=N` importa e associa un WAV.
