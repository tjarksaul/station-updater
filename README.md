# station-updater
Ein Client, um ein auf einem Raspberry Pi laufendes Temperaturmonitoring an den Stationsstatus auf dlrg.net anzubinden.

# Hardware
<FOTO EINSETZEN>

## Einkaufsliste

## Schaltplan
Hier folgt ein detaillierter Schaltplan, hier erst mal ein Foto meines Setups. Ich habe dafür ein IKEA MOPPE Kommödchen genutzt, geht aber natürlich auch beliebig anders.


# Software

## Setup 
```bash
pip install virtualenv
virtualenv -p python2.7 .environment
source .environment/bin/activate
pip install -r requirements.txt
```

Dieses virtualenv sollte dann irgendwie mithilfe eines Taskamanagers (z.B. daemontools oder systemd) automatisch gestartet werden.

## Einstellungen
Alle Einstellungen werden in einer env-File hinterlegt, können aber auch direkt als Environment-Variablen übergeben werden. Für die env-File einfach mit `cp .env.default .env` kopieren und dann die .env entsprechend bearbeiten, die einzelnen Werte ergeben sich schnell. 
