# SimKorg e manuale Korg electribe sampler

Riferimento: `maunal.pdf` nel repository, manuale ufficiale Korg *electribe/electribe sampler*, sezione inglese pp. 4–19. Questa pagina indica cosa fa la replica dopo l'aggiornamento e dove si discosta dallo strumento fisico. Il PDF descrive anche controlli di alimentazione, connettori e schede SD che non hanno equivalenti in un'app web.

## Funzioni disponibili

| Sezione del manuale | Comportamento SimKorg |
| --- | --- |
| Pattern e parti (pp. 8–9) | 250 slot JSON; 16 parti per pattern; scelta dello slot con Pattern/Value e caricamento con Menu/Enter. WRITE salva nello slot corrente. |
| Pad Trigger/Sequencer/Keyboard/Chord/Step Jump/Pattern Set (pp. 5–6, 10–12) | Sei modi dei pad; il sequencer mostra 16 step per pagina. I tasti step 1–4 scelgono la pagina, o l'ottava in Keyboard/Chord, o il gruppo in Pattern Set. |
| Beat e Length (p. 13) | Lunghezza da una a quattro battute da Funzioni SimKorg → Battute. Ogni battuta ha 16 step. Swing è regolabile; il beat resta in sedicesimi. |
| Key e Scale (pp. 10, 13) | Tonalità cromatica e scale maggiore, minore, pentatonica o cromatica da Funzioni SimKorg. Si applicano ai pad Keyboard/Chord e al touch scale. |
| Pattern Level (p. 13) | Livello generale del pattern da Funzioni SimKorg. |
| Parametri delle parti (p. 5) | I valori delle manopole sono memorizzati per ogni parte; selezionando una parte il pannello mostra i suoi valori. Il livello, il pitch, l'inviluppo e alcuni parametri del campione vengono applicati alle nuove voci. Volume, Input Level, BPM e Swing restano comuni. |
| Metronomo (p. 14) | Spento, sempre attivo durante PLAY, oppure solo durante REC, da Funzioni SimKorg. Clic ogni quarto. |
| Sample Edit (pp. 16–17) | Per i WAV assegnati: punto di inizio da 0 a 95% e riproduzione avanti/reverse, per parte. L'impostazione agisce sulle nuove note. |
| Registrazione e motion (p. 12) | REC registra trigger sui passi; Motion registra i valori delle manopole sui passi. Salvataggio nel pattern. |
| Part Mute/Erase/Copy (p. 13) | Mute, cancellazione step, copia e incolla di step e valori della parte. |
| WAV personali (pp. 16–17) | Importazione WAV PCM, associazione ai pad e salvataggio del nome nel pattern. I file restano nella cartella `samples/`. |

## Procedura rapida

1. Avvia il server come nel README e apri il pannello.
2. In **Funzioni SimKorg** scegli **Battute**, **Tonalità**, **Scala** e **Livello pattern**.
3. Premi **SEQUENCER**, seleziona la parte, scegli una pagina con i pulsanti step **1–4** e attiva gli step con i pad.
4. Premi **PLAY/PAUSE**. Con **REC** puoi registrare i pad Trigger durante la riproduzione.
5. Salva con **WRITE**. Per cambiare slot usa **Pattern** e ruota **Value**, poi premi **MENU/ENTER** per caricare o **WRITE** per salvare.

## Formato e compatibilità

I file `patterns/pattern_01.json` … `pattern_250.json` salvano `version: 2`, 64 step per parte, lunghezza, tonalità, scala, livello, metronomo e valori delle parti. I file esistenti a 16 step/versione 1 si caricano: i passi mancanti vengono considerati spenti e i parametri aggiunti ricevono i valori predefiniti. Gli slot 1–99 mantengono il nome a due cifre per compatibilità. Le assegnazioni Pattern Set restano in `patterns/pattern_sets.json`.

## Differenze ancora presenti rispetto all'hardware

La replica non implementa tutto il firmware. Restano fuori sampling diretto dall'ingresso, resampling, slice/loop avanzati, streaming stereo dei sample, filtri ed effetti indipendenti per parte, diversi tipi di groove/beat, chain repeat/chain to, event recorder, import/export SD e Ableton, MIDI/USB/Sync, registrazione motion Smooth/Trigger Hold, undo e utilità di sistema. Il filtro, il pan e gli effetti sono elaborati principalmente sul mix; alcuni controlli di parte sono memorizzati ma non hanno ancora un percorso audio separato. Il manuale PDF menziona inoltre una *Parameter Guide* distinta, non presente nel repository: i parametri descritti solo lì non sono specificati abbastanza per riprodurli fedelmente.

La cartella `samples/` non è versionata; per trasferire pattern con WAV personali occorre copiare anche quei file.
