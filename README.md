```txt
anpr/
├── docker-compose.yml          # Docker services (MariaDB + MQTT)
├── .env                        # Miljøvariabler (passwords)
├── README.md                   # Projekt dokumentation
│
├── mqtt-broker/
│   ├── mosquitto.conf            # MQTT broker konfiguration
│   └── passwordfile              # MQTT bruger passwords
│
├── pc-side/                      # Bærbar PC med kamera
│   ├── src/
│   │   ├── main.py               # Hovedprogram - koordinerer alt
│   │   ├── license_plate_recognizer.py  # ML nummerpladegenkendelse
│   │   ├── database_handler.py   # MariaDB kommunikation
│   │   ├── flatfiledb.py         # json db
│   │   └── mqtt_publisher.py     # MQTT publishing til Raspberry Pi
│   ├── config/
│   │   ├── config.yaml           # Konfiguration (kamera, DB, MQTT)
│   │   └──
|   |   └── ssl 
|   |       └──ca.crt             # Bruges til at validere broker
|   |       └──client.crt         # clienten's eget certifikat
|   |       └──client.key         # Clienten's private nøgle
│   ├── requirements.txt          # Python afhængigheder
│   └── Dockerfile                # Containerisering (valgfri)
│
├── raspberry-pi-side/         # Raspberry Pi ved parkeringspladsen
│   ├── src/
│   │   ├── main.py               # Hovedprogram - starter MQTT subscriber
│   │   ├── mqtt_subscriber.py    # MQTT subscribing fra PC
│   │   ├── display_manager.py    # OLED display kontrol (SSD1306)
│   │   └── gate_controller.py    # Servo motor kontrol til bom
│   ├── config/
│   │   └── config.yaml           # Konfiguration (MQTT, GPIO, display)
|   |   └── ssl 
|   |       └──ca.crt             # Bruges til at validere broker
|   |       └──rasp.crt           # Raspberry's eget certifikat
|   |       └──rasp.key           # Raspberry's private nøgle
│   ├── requirements.txt          # Python afhængigheder
│   
│
└── shared/
    ├── ssl/
    |   ├──broker
    |   |  └──broker.crt # Server-certifikat - Identificerer brokeren for klienter
    |   |  └──broker.csr # Certificate Signing Request - Brugt til at få cert underskrevet af CA
    |   |  └──broker.key # Privat server-nøgle - Til TLS-autentifikation
    ├── ssl/
    |   ├──ca
    |   |  └──ca.crt  # Offentligt certifikat - Distribueres til alle klienter for validering
    |   |  └──ca.srl  # Serial Number List - Trackser udstedte serienumre
    |   |  └──ca.key  # Privat nøgle - Bruges til at underskrive andre certifikater
    ├── ssl/
    |   ├──client
    |   |  └──kamera
    |   |     └──client.crt # Klient-certifikat - Verificerer PC'ens identitet
    |   |     └──client.csr # CSR for klient - Anmodning om klientcertifikat
    |   |     └──client.key # Privat klient-nøgle - Til klient-autentifikation mod broker
    |   |  └──rasp
    |   |     └──rasp.crt
    |   |     └──rasp.csr
    |   |     └──rasp.key

    └── sql/
        └── init_database.sql 
```

