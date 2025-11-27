 Det her er nuværende status på projektet det kører unde TLS men kommunikation mellem raspberry og broker virker fint. Jeg har lavet en nummerplade simulator så vi kan implementere vores egen rigtige anpg kode. Alle nummerplader bliver også indsat i databasen samt tidspunkt
 MQTT og mariaDB kører som 0services  
```txt
anpr/
├── 🐳 docker-compose.yml          # Docker services (MariaDB + MQTT)
├── 🔐 .env                        # Miljøvariabler (passwords)
├── 📖 README.md                   # Projekt dokumentation
│
├── 📡 mqtt-broker/
│   ├── mosquitto.conf            # MQTT broker konfiguration
│   └── passwordfile              # MQTT bruger passwords
│
├── 💻 pc-side/                    # Bærbar PC med kamera
│   ├── src/
│   │   ├── main.py               # Hovedprogram - koordinerer alt
│   │   ├── license_plate_recognizer.py  # ML nummerpladegenkendelse test udgave lige nuuu
│   │   ├── database_handler.py   # MariaDB kommunikation
│   │   └── mqtt_publisher.py     # MQTT publishing til Raspberry Pi
│   ├── config/
│   │   ├── config.yaml           # Konfiguration (kamera, DB, MQTT)
│   │   └── cascade.xml           # Haar Cascade til OpenCV
│   ├── requirements.txt          # Python afhængigheder
│   └── Dockerfile                # Containerisering (valgfri)
│
├── 🍓 raspberry-pi-side/         # Raspberry Pi ved parkeringspladsen
│   ├── src/
│   │   ├── main.py               # Hovedprogram - starter MQTT subscriber
│   │   ├── mqtt_subscriber.py    # MQTT subscribing fra PC
│   │   ├── display_manager.py    # OLED display kontrol (SSD1306)
│   │   └── gate_controller.py    # Servo motor kontrol til bom
│   ├── config/
│   │   └── config.yaml           # Konfiguration (MQTT, GPIO, display)
│   ├── requirements.txt          # Python afhængigheder
│   └── start.sh                  # Startup script
│
└── 🔗 shared/
    ├── ssl/                      # TLS certifikater (ikke i brug lige nu)
    └── sql/
        └── init_database.sql     # Database schema opsætning
```


docker-compose.yml
services:
  mariadb:
    image: mariadb:latest
    ports: ["3306:3306"]
    env_file: .env
    volumes:
      - db_data:/var/lib/mysql
      - ./shared/sql/init_database.sql:/docker-entrypoint-initdb.d/init_database.sql

  mqtt-broker:
    image: eclipse-mosquitto:latest
    ports: ["1883:1883"]  # Standard MQTT (uden TLS)
    volumes:
      - ./mqtt-broker/mosquitto.conf:/mosquitto/config/mosquitto.conf



.env
DB_ROOT_PASSWORD=supersecretroot
DB_NAME=parking_system
DB_USER=parking_user
DB_PASSWORD=parking_password123




mqtt-broker/mosquitto.conf
listener 1883
allow_anonymous true
log_dest stdout


pc-side/config/config.yaml
camera:
  source: 0
  width: 640
  height: 480

database:
  host: "localhost"
  port: 3306
  user: "parking_user"
  password: "parking_password123"
  database: "parking_system"

mqtt:
  broker: "localhost"
  port: 1883
  client_id: "pc_camera"
  topics:
    parking_events: "parking/events"
    available_spots: "parking/available_spots"

license_plate:
  cascade_file: "config/cascade.xml"
  confidence_threshold: 0.8




raspberry-pi-side/config/config.yaml
mqtt:
  broker: "10.0.0.10"  # PC'ens IP adresse
  port: 1883
  client_id: "raspberry_pi"
  topics:
    available_spots: "parking/available_spots"
    gate_control: "parking/gate_control"

display:
  type: "oled"
  width: 128
  height: 64

gate:
  control_pin: 17
  open_time: 3  # sekunder

servo:
  pin: 18
  open_angle: 90
  close_angle: 0



shared/sql/init_database.sql
CREATE TABLE license_plates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parking_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20),
    event_type ENUM('entry', 'exit'),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parking_spots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    spot_number INT NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE,
    plate_number VARCHAR(20),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);




Start Commands
Start infrastruktur:
bash

docker-compose up -d

Start PC simulator:
bash

cd pc-side
pip install -r requirements.txt
python src/main.py

Start Raspberry Pi:
bash

cd raspberry-pi-side
pip install -r requirements.txt
python src/main.py

Test MQTT:
bash

# Monitor MQTT trafik
docker run --rm --network anpr_parking_network eclipse-mosquitto mosquitto_sub -h parking_mqtt_broker -t "parking/#" -v




Nøgle Funktionalitet
PC-side:

    Simulerer nummerpladegenkendelse (kan erstattes med rigtig ML)

    Gemmer data i MariaDB

    Publisher MQTT beskeder ved parkeringsbegivenheder

    Opdaterer ledige pladser (200 totale pladser)

Raspberry Pi-side:

    Subscriber til MQTT beskeder

    Viser ledige pladser på OLED display

    Åbner servo-bom automatisk når biler kører UD

    Viser "FULD" når der er 0 ledige pladser

MQTT Topics:

    parking/available_spots - JSON med ledige pladser

    parking/events - Parkeringsbegivenheder (entry/exit)

    parking/gate_control - Bom kontrol




MB@ADMIN MINGW64 /c/workspace/anpr/pc-side
$ docker compose down
[+] Running 3/3
 ✔ Container parking_mqtt_broker  Removed                           0.4s 
 ✔ Container parking_db           Removed                           0.5s 
 ✔ Network anpr_parking_network   Removed  
