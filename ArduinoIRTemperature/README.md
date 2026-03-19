# Arduino IR Temperature

Este proyecto lee temperaturas desde un Arduino por puerto serial y guarda los datos en un archivo CSV usando `getTemperature.py`.

El script Python está configurado para guardar una lectura válida cada 30 segundos en el CSV, en sincronía con el intervalo de muestreo del Arduino.

## Ejecutar `getTemperature.py` al arrancar una Raspberry Pi

La forma recomendada es configurarlo como un servicio de `systemd`.

## 1. Instalar dependencias

```bash
sudo apt update
sudo apt install -y python3 python3-pip
pip3 install pyserial
```

## 2. Copiar el proyecto a una ruta fija

Ejemplo:

```bash
/home/pi/ArduinoIRTemperature/
```

El script debería quedar en:

```bash
/home/pi/ArduinoIRTemperature/getTemperature.py
```

## 3. Probar el script manualmente

Antes de automatizarlo, verifica que funciona:

```bash
python3 /home/pi/ArduinoIRTemperature/getTemperature.py -p /dev/ttyACM0 --csv /home/pi/ArduinoIRTemperature/temperaturas.csv
```

Si tu Arduino aparece con otro nombre, usa por ejemplo `/dev/ttyUSB0`.

Si quieres definir explícitamente el intervalo de escritura:

```bash
python3 /home/pi/ArduinoIRTemperature/getTemperature.py -p /dev/ttyACM0 --csv /home/pi/ArduinoIRTemperature/temperaturas.csv --sample-interval 30
```

## 4. Crear el servicio de `systemd`

Crea el archivo:

```bash
sudo nano /etc/systemd/system/arduino-temp.service
```

Contenido sugerido:

```ini
[Unit]
Description=Lectura de temperatura desde Arduino
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ArduinoIRTemperature
ExecStart=/usr/bin/python3 /home/pi/ArduinoIRTemperature/getTemperature.py -p /dev/ttyACM0 --csv /home/pi/ArduinoIRTemperature/temperaturas.csv
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 5. Activar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable arduino-temp.service
sudo systemctl start arduino-temp.service
```

## 6. Verificar que esté funcionando

```bash
sudo systemctl status arduino-temp.service
journalctl -u arduino-temp.service -f
```

## 7. Dar permisos al puerto serial

El usuario que ejecuta el servicio debe tener acceso al puerto serial:

```bash
sudo usermod -a -G dialout pi
```

Después reinicia la Raspberry Pi para aplicar el cambio de grupo.

## Notas

- Usa rutas absolutas en el servicio.
- El puerto serial suele ser `/dev/ttyACM0` o `/dev/ttyUSB0`.
- El script espera líneas con el formato `temp_ambiente,temp_objeto`.
- El script limpia el buffer serial al arrancar y toma la primera lectura válida como referencia.
- Después de eso, solo guarda una fila por cada `30` segundos. Si cambias el intervalo en el Arduino, usa `--sample-interval` con el mismo valor en la Raspberry Pi.
- Si el archivo CSV se borra mientras el script está corriendo, el proceso detecta la ausencia del archivo, lo recrea y sigue escribiendo en la misma ruta.
