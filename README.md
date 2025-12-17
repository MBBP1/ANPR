 Det her er nuværende status på projektet det kører unde TLS men kommunikation mellem raspberry og broker virker fint. Jeg har lavet en nummerplade simulator så vi kan implementere vores egen rigtige anpg kode. Alle nummerplader bliver også indsat i databasen samt tidspunkt
 MQTT og mariaDB kører som 0services  
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
|   |       └──ca.crt
|   |       └──client.crt
|   |       └──client.key
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
|   |       └──ca.crt
|   |       └──rasp.crt
|   |       └──rasp.key
│   ├── requirements.txt          # Python afhængigheder
│   
│
└── shared/
    ├── ssl/
    |   ├──broker
    |   |  └──broker.crt
    |   |  └──broker.csr
    |   |  └──broker.key
    ├── ssl/
    |   ├──ca
    |   |  └──ca.crt
    |   |  └──ca.srl
    |   |  └──ca.key
    ├── ssl/
    |   ├──client
    |   |  └──kamera
    |   |     └──client.crt
    |   |     └──client.csr
    |   |     └──client.key
    |   |  └──rasp
    |   |     └──rasp.crt
    |   |     └──rasp.csr
    |   |     └──rasp.key

    └── sql/
        └── init_database.sql 
```

