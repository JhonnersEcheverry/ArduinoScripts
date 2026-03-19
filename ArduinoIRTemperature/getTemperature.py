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
from time import monotonic, sleep
import serial
from serial import SerialException


DEFAULT_SAMPLE_INTERVAL = 30.0


def parse_temperatures(line: str) -> tuple[float, float]:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 2:
        raise ValueError("Se esperaban 2 valores separados por coma")
    return float(parts[0]), float(parts[1])


def wait_for_arduino_reset() -> None:
    """Da tiempo al Arduino a reiniciar cuando se abre el puerto serial."""
    sleep(2.5)


def should_store_reading(
    now_monotonic: float, last_saved_monotonic: float | None, interval_seconds: float
) -> bool:
    if last_saved_monotonic is None:
        return True
    return (now_monotonic - last_saved_monotonic) >= interval_seconds


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
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=DEFAULT_SAMPLE_INTERVAL,
        help="Intervalo mínimo entre filas guardadas en CSV, en segundos (default: 30)",
    )
    args = parser.parse_args()

    try:
        csv_exists = os.path.exists(args.csv)
        with (
            serial.Serial(args.port, args.baudrate, timeout=args.timeout) as ser,
            open(args.csv, "a", newline="", encoding="utf-8") as csv_file,
        ):
            wait_for_arduino_reset()
            ser.reset_input_buffer()

            writer = csv.writer(csv_file)
            if not csv_exists or os.path.getsize(args.csv) == 0:
                writer.writerow(["timestamp", "temp_ambiente", "temp_objeto"])
                csv_file.flush()

            last_saved_monotonic: float | None = None
            print(
                f"Escuchando {args.port} a {args.baudrate} baud. "
                "Esperando: TempAmbiente,TempObjeto"
            )
            print(f"Guardando lecturas en: {args.csv}")
            print(
                f"Sincronizando una fila cada {args.sample_interval:.0f} segundos "
                "a partir de la primera lectura valida."
            )
            while True:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    temp_ambiente, temp_objeto = parse_temperatures(line)
                    now_monotonic = monotonic()
                    if not should_store_reading(
                        now_monotonic,
                        last_saved_monotonic,
                        args.sample_interval,
                    ):
                        continue

                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([ts, temp_ambiente, temp_objeto])
                    csv_file.flush()
                    last_saved_monotonic = now_monotonic
                    print(
                        f"{ts} | TempAmbiente={temp_ambiente:.2f} °C, "
                        f"TempObjeto={temp_objeto:.2f} °C"
                    )
                except ValueError:
                    print(f"Línea inválida: {line}", file=sys.stderr)
    except SerialException as exc:
        print(f"Error serial: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nLectura detenida por usuario.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
