# electribe sampler — replica interattiva

Replica ispirata alla foto fornita. Il pannello è in `static/index.html` (HTML, CSS e JavaScript vanilla); WebSocket, clock, sequencer e sintesi audio sono in Python. Non è un'emulazione completa del firmware Korg.

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

L'audio esce dal computer che esegue il server. Per ascoltarlo anche sul dispositivo che apre la pagina, tocca **Ascolta su questo dispositivo**. Aprendo direttamente `static/index.html` si vede il pannello, ma audio e sequencer richiedono il server. Se non senti nulla, controlla uscita audio, tasto Power e manopola Volume. Se il display segnala un errore audio, verifica che sia disponibile un dispositivo di uscita. La manopola Input Level richiede anche un ingresso audio disponibile.

## Ascolto su iPad

1. Collega iPad e computer alla stessa rete Wi-Fi.
2. Sul computer avvia il server con `--host 0.0.0.0` invece di `--host 127.0.0.1`. Esempio macOS/Linux: `.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000`.
3. Trova l'indirizzo IP locale del computer e su Safari apri `http://INDIRIZZO-IP:8000/`.
4. Tocca **Ascolta su questo dispositivo**. Questo gesto è necessario per consentire a Safari di avviare l'audio. Tieni la pagina in primo piano mentre suoni.

Il computer può suonare insieme all'iPad; abbassa il suo volume se senti un doppio audio. Se Safari non si collega, controlla il firewall e che la rete Wi-Fi non isoli i dispositivi tra loro. Il flusso audio usa la rete locale e può avere un piccolo ritardo rispetto ai comandi.

## Uso

- Trascinare le manopole verso l'alto o il basso, usare la rotella oppure i tasti freccia. Doppio clic per il valore iniziale.
- Suonare i pad con mouse, tocco o tastiera: `1`–`8` per la prima riga, `Q W E R T Y U I` per la seconda.
- `SEQ` mostra gli step della parte selezionata. Un clic cambia lo step; `PLAY` avvia il clock, `STOP` lo ferma, `REC` registra i colpi suonati sulla posizione corrente. `◀ PART` e `PART ▶` cambiano parte.
- `GATE`, `SCALE`, `MFX` selezionano la funzione del touch pad. `HOLD` mantiene l'effetto MFX dopo il rilascio.
- `TAP` calcola il BPM dalla cadenza dei clic. Anche la manopola BPM lo modifica. La manopola Swing varia il tempo degli step alterni.
- Il tasto `FX` alterna delay e distorsione; la manopola FX Depth regola l'effetto scelto. `POWER` silenzia il motore e ferma il sequencer.
- I tre pulsanti verticali a destra sono `▲` e `▼` per scorrere parametri o slot dei pattern, e `+` per cambiare il valore. `SHIFT` insieme a `+` diminuisce il valore. `MENU` apre l'elenco; `FILTER`, `MOD` e `AMP` aprono direttamente la rispettiva sezione. `ENTER` conferma o carica il pattern selezionato; `EXIT` chiude il menu.
- `PART SELECT` trasforma i pad in selettori delle 16 parti. `MUTE` silenzia la parte nel sequencer. `COPY` e `PASTE` duplicano gli step; `ERASE` cancella quelli della parte. `SHIFT` + `ERASE` cancella gli step di tutte le parti. `MOTION` attiva la registrazione e riproduzione dei movimenti delle manopole sugli step; spegnendolo si disattiva l'automazione. La riproduzione modifica il suono, senza muovere graficamente le manopole manuali.
- `WRITE` salva il pattern nello slot corrente in `patterns/`. `PATTERN` apre gli slot 1–16; usare `▲`/`▼` e `ENTER` per ricaricare uno slot, oppure `WRITE` per salvare in quello selezionato.
- Per usare campioni personali, toccare il pad da assegnare e premere `SAMPLE_EDIT`: si può scegliere un WAV già presente in `samples/` oppure importarne uno dal dispositivo. Sono accettati WAV PCM non compressi fino a 20 secondi e 20 MB.

La manopola `Input Level` regola il monitoraggio dell'ingresso audio del computer che esegue il server, se il dispositivo audio lo consente. La scritta minuta e alcune posizioni sono approssimate perché la foto da 447×447 pixel non consente di distinguerle con precisione. Le funzioni implementate sono una replica d'uso, non una copia del firmware Korg.

## Protocollo

`/ws` riceve eventi JSON `knob`, `pad`, `touch` e `button`; invia `state` con BPM, step, parte, modalità, LED, valori e due righe del display. `/audio` invia PCM stereo 16 bit/44,1 kHz al browser; l'interfaccia lo riproduce senza sintetizzarlo. `GET /api/samples` elenca i WAV; `POST /api/assign` associa un file a un pad; `POST /api/upload/{filename}?index=N` importa e associa un WAV.
