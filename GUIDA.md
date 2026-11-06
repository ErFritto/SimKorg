# Guida completa a SimKorg electribe sampler

Questa guida descrive la replica **SimKorg**. Per il confronto con il manuale ufficiale, le funzioni aggiunte e i limiti, vedi [MANUALE_IMPLEMENTAZIONE.md](MANUALE_IMPLEMENTAZIONE.md). Il pannello è ispirato al Korg electribe sampler, ma non riproduce tutto il firmware dello strumento fisico. Le 16 parti condividono le manopole audio; ogni parte ha i propri 16–64 step e un eventuale campione WAV.

## 1. Avvio e audio

Segui i comandi di installazione nel [README](README.md), avvia il server e apri `http://127.0.0.1:8000/`. Il suono esce dal computer che esegue Python. Se usi un altro dispositivo, premi **Ascolta su questo dispositivo** sulla pagina aperta lì. Se senti lo stesso suono da due dispositivi vicini, abbassa il volume di uno dei due.

Il **microfono del computer è spento all'avvio**. Premi **Attiva microfono** soltanto se vuoi ascoltare l'ingresso audio del computer attraverso la replica. **Input Level** regola quanto ingresso viene sommato al suono dei pad; a zero il microfono non è udibile. Premi **Disattiva microfono** per chiudere l'ingresso. Spegnere **POWER** lo disattiva. Il microfono usato è quello del computer che esegue il server, anche se controlli la pagina da iPad. Il browser non chiede accesso al microfono.

Per evitare fischi o eco quando attivi il microfono, usa cuffie oppure tieni gli altoparlanti lontani dal microfono.

## 2. Suonare subito

1. Verifica che **POWER** sia acceso e alza **Volume**.
2. Premi **TRIGGER** per usare i 16 pad come strumenti.
3. Tocca un pad. Le parti 1, 5, 9 e 13 sono kick; 2, 6, 10 e 14 snare; 3, 7, 11 e 15 hi-hat; 4, 8, 12 e 16 clap, finché non assegni campioni diversi.
4. Premi **PLAY/PAUSE** per avviare il pattern. **STOP** lo ferma e riporta la posizione all'inizio.

Con la tastiera, `1`–`8` suonano la prima riga; `Q W E R T Y U I` la seconda. I pad rispondono anche al mouse o al tocco. Il punto in cui premi un pad cambia leggermente la velocity.

## 3. Manopole e parametri

Trascina una manopola verso l'alto o il basso, usa la rotella del mouse o le frecce della tastiera dopo averla selezionata. Doppio clic ripristina il valore iniziale mostrato all'apertura della pagina. Volume, Input Level, BPM e Swing sono globali; le altre manopole sono memorizzate per parte. Alcuni effetti restano elaborati sul mix: vedi [MANUALE_IMPLEMENTAZIONE.md](MANUALE_IMPLEMENTAZIONE.md).

| Controllo | Effetto |
| --- | --- |
| Volume | Livello complessivo dell'uscita. |
| Input Level | Livello del microfono, solo quando lo attivi esplicitamente. |
| Sample | Livello dei WAV assegnati ai pad. |
| Pitch | Intonazione delle note generate dal touch pad in modalità SCALE o GATE. |
| Filter, Resonance, LPF/HPF/BPF | Frequenza, enfasi e tipo del filtro globale: passa basso, passa alto o passa banda. |
| Rate, LFO Depth, LFO Shape | Velocità, intensità e forma della modulazione: sinusoidale, triangolare o quadra. |
| Level, Pan | Livello dopo gli effetti e posizione tra canale sinistro e destro. |
| Attack, Decay | Attacco delle note del touch pad e durata del loro decadimento. |
| FX Depth, FX Time | Quantità dell'effetto e tempo del delay. |
| BPM, Swing | Velocità da 40 a 240 BPM e alternanza ritmica degli step; sono nei controlli **Funzioni SimKorg**. |

**MFX SEND** abilita l'effetto del touch pad MFX. **AMP EG** abilita l'inviluppo delle note. **IFX ON** abilita la distorsione quando selezionata. La scelta tra delay e distorsione è in **Funzioni SimKorg**. In modalità delay, **FX Depth** regola la quantità di ripetizioni udibili e **FX Time** la distanza tra le ripetizioni. In modalità distorsione, **FX Depth** regola la spinta. **TAP** imposta il tempo in base alla cadenza dei tocchi. I tre interruttori hanno effetto globale nella replica.

## 4. Creare un pattern di 16 step

1. Premi **◀ PART** o **PART ▶** per scegliere una delle 16 parti. Puoi anche usare **Seleziona parte** in **Funzioni SimKorg** e poi un pad.
2. Premi **SEQUENCER**. I pad rappresentano 16 step della pagina scelta con i tasti step 1–4. Imposta da una a quattro battute in **Funzioni SimKorg**. Tocca uno step per accenderlo o spegnerlo.
3. Premi **PLAY/PAUSE**. L'indicatore avanza sugli step; quando incontra uno step acceso, suona la parte corrispondente.
4. Scegli un'altra parte e aggiungi i suoi step. Premi **TRIGGER** per tornare a suonare i pad.

**REC** abilita la registrazione dal vivo: con PLAY attivo e in modalità TRIGGER, ogni pad suonato viene scritto nella posizione corrente della rispettiva parte. Premi di nuovo REC per uscire dalla registrazione. **PART MUTE** trasforma i pad in interruttori per silenziare o riattivare le parti. **PART ERASE** trasforma i pad in selettori della parte da cancellare. Con **SHIFT** acceso, premere PART ERASE cancella gli step di tutte le parti. Premi SHIFT ancora per spegnerlo. **Copia parte** e **Incolla parte** sono in **Funzioni SimKorg**.

**Motion**, in **Funzioni SimKorg**, attiva la registrazione e la riproduzione dei movimenti delle manopole durante PLAY. Quando muovi un parametro, il suo valore viene salvato sullo step corrente. Gli step automatizzati modificano il suono senza muovere graficamente le manopole. Premi di nuovo Motion per disattivare l'automazione. Volume, Input Level, BPM e Swing non vengono registrati come motion.

## 5. Nuovi modi dei pad e pulsanti step

| Pulsante | Funzione nella replica |
| --- | --- |
| TRIGGER | Ogni pad suona la propria parte. |
| SEQUENCER | Ogni pad accende o spegne uno step della parte scelta. |
| KEYBOARD | I 16 pad suonano note della parte scelta. |
| CHORD | I 16 pad suonano accordi di tre note. |
| STEP JUMP | Durante PLAY, un pad sposta immediatamente la riproduzione allo step corrispondente. |
| PATTERN SET | Ogni pad carica il pattern assegnato a quella posizione. |

I pulsanti **1–4** a destra scelgono la pagina da 16 step in SEQUENCER, la trasposizione di ottava in KEYBOARD e CHORD, oppure il gruppo di 16 pad in PATTERN SET. Per registrare un pattern in PATTERN SET, seleziona prima lo slot da **Funzioni SimKorg → Pattern**, scegli il gruppo 1–4, accendi **SHIFT** e tocca il pad di destinazione. Spegni SHIFT per richiamare i pattern toccando i pad. Le assegnazioni sono salvate in `patterns/pattern_sets.json`.

## 6. Touch pad

Scegli una modalità con i pulsanti sopra i pad, poi trascina il dito o il mouse sull'area touch:

| Modalità | Uso |
| --- | --- |
| SCALE | Suona note di una scala pentatonica; la posizione orizzontale sceglie la nota e quella verticale influisce sulla velocity. |
| GATE | Ripete una nota automaticamente mentre tocchi; la posizione verticale cambia la velocità delle ripetizioni. |
| MFX | La posizione orizzontale modifica il cutoff del filtro, quella verticale la quantità di delay. |
| HOLD | Mantiene l'ultima posizione MFX anche dopo aver tolto il dito. Premilo di nuovo per rilasciarla. |

## 7. Usare campioni WAV personali

1. In modalità TRIGGER, tocca il pad a cui vuoi assegnare il campione. Puoi anche usare il relativo tasto della tastiera.
2. Apri **Funzioni SimKorg** e premi **Importa WAV**.
3. Scegli il nome di un WAV già presente nella cartella `samples/`, oppure scrivi `IMPORTA` per scegliere un file dal dispositivo. Se la cartella è vuota, si apre direttamente la selezione file.
4. Suona il pad: il WAV sostituisce il suono sintetico di quella parte. Regola **Sample** per cambiarne il livello.

Sono accettati WAV PCM non compressi a 8, 16 o 32 bit, lunghi al massimo 20 secondi e di dimensione inferiore a 20 MB. I canali stereo vengono mescolati in mono. Se carichi un file con un nome già esistente, rinominalo prima di importarlo. Per mantenere l'associazione dopo un riavvio, salva il pattern con WRITE e conserva il WAV nella cartella `samples/`.

## 8. Menu e salvataggio

**MENU/ENTER** apre l'elenco dei parametri o conferma. **‹** e **›** scorrono le voci. Ruota **Value** trascinando verticalmente la manopola, usando la rotella del mouse o i tasti freccia: cambia il valore mostrato. **EXIT** chiude. I parametri principali si regolano anche dalle manopole.

**WRITE** salva lo stato nello slot corrente, in `patterns/pattern_NN.json`. Ruota **Value** dalla schermata iniziale, oppure premi **Pattern** in **Funzioni SimKorg**, per scegliere uno slot da 1 a 250; premi **MENU/ENTER** per caricarlo oppure **WRITE** per salvarci lo stato corrente. Se lo slot è vuoto, il display mostra `EMPTY SLOT`. Il file salva step, mute, valori delle manopole, tipo di effetto, stato MFX SEND/AMP EG/IFX ON, motion e nomi dei WAV assegnati. L'attivazione del microfono non viene salvata: resta spenta al prossimo avvio. Salva prima di chiudere il server o passare a un altro pattern.

## 9. Se qualcosa non funziona

| Sintomo | Controllo |
| --- | --- |
| Non senti i pad | Controlla POWER, Volume, Level, uscita audio del computer e messaggi sotto il pannello. Se ascolti da iPad, premi anche **Ascolta su questo dispositivo**. |
| Senti la tua voce | Premi **Disattiva microfono**. Se il microfono è già spento, verifica il monitoraggio audio del sistema operativo o di altre applicazioni. |
| Senti eco o fischio | Disattiva il microfono o usa cuffie. Se ascolti da due dispositivi, silenziane uno. |
| Un pad del sequencer non suona | Controlla gli step della sua parte, MUTE, Volume e il WAV eventualmente assegnato. |
| Il WAV non viene caricato | Verifica formato PCM, durata, dimensione e nome del file. |
| La pagina si vede ma non risponde | Apri l'indirizzo del server, non direttamente `static/index.html`; verifica che il terminale con uvicorn sia ancora aperto. |
