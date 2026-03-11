#!/usr/bin/env python3
"""Lee temperaturas desde Arduino por serial a 9600 baud.

Formato esperado por línea:
    TempAmbiente,TempObjeto
Ejemplo:
    24.8,31.2
"""

import argparse
import csv
import os
import sys
from datetime import datetime
import serial


def parse_temperatures(line: str) -> tuple[float, float]:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 2:
        raise ValueError("Se esperaban 2 valores separados por coma")
    return float(parts[0]), float(parts[1])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lee TempAmbiente y TempObjeto desde Arduino por serial."
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        help="Puerto serial (ej: COM3, /dev/ttyACM0, /dev/ttyUSB0)",
    )
    parser.add_argument(
        "-b",
        "--baudrate",
        type=int,
        default=9600,
        help="Baudrate serial (default: 9600)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1.0,
        help="Timeout de lectura en segundos (default: 1.0)",
    )
    parser.add_argument(
        "--csv",
        default="temperaturas.csv",
        help="Ruta del archivo CSV de salida (default: temperaturas.csv)",
    )
    args = parser.parse_args()

    try:
        csv_exists = os.path.exists(args.csv)
        with (
            serial.Serial(args.port, args.baudrate, timeout=args.timeout) as ser,
            open(args.csv, "a", newline="", encoding="utf-8") as csv_file,
        ):
            writer = csv.writer(csv_file)
            if not csv_exists or os.path.getsize(args.csv) == 0:
                writer.writerow(["timestamp", "temp_ambiente", "temp_objeto"])
                csv_file.flush()

            print(
                f"Escuchando {args.port} a {args.baudrate} baud. "
                "Esperando: TempAmbiente,TempObjeto"
            )
            print(f"Guardando lecturas en: {args.csv}")
            while True:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    temp_ambiente, temp_objeto = parse_temperatures(line)
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([ts, temp_ambiente, temp_objeto])
                    csv_file.flush()
                    print(
                        f"{ts} | TempAmbiente={temp_ambiente:.2f} °C, "
                        f"TempObjeto={temp_objeto:.2f} °C"
                    )
                except ValueError:
                    print(f"Línea inválida: {line}", file=sys.stderr)
    except serial.SerialException as exc:
        print(f"Error serial: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nLectura detenida por usuario.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
