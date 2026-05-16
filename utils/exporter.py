import cv2
import json
import csv
from pathlib import Path
from typing import List, Tuple
from utils.logger import app_logger


class Exporter:
    @staticmethod
    def save_image(img, path: str) -> bool:
        try:
            cv2.imwrite(path, img)
            app_logger.info(f"Imagen guardada: {path}")
            return True
        except Exception as e:
            app_logger.error(f"Error guardando imagen: {e}")
            return False

    @staticmethod
    def save_csv(points: List[Tuple[int, int]], path: str, metadata: dict = None) -> bool:
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["x", "y", "id"])
                for idx, (x, y) in enumerate(points, 1):
                    writer.writerow([x, y, idx])

                if metadata:
                    writer.writerow([])
                    for key, value in metadata.items():
                        writer.writerow([key, value])

            app_logger.info(f"CSV guardado: {path}")
            return True
        except Exception as e:
            app_logger.error(f"Error guardando CSV: {e}")
            return False

    @staticmethod
    def save_json(points: List[Tuple[int, int]], path: str, metadata: dict = None) -> bool:
        try:
            data = {
                "count": len(points),
                "detections": [{"id": i+1, "x": x, "y": y} for i, (x, y) in enumerate(points)]
            }
            if metadata:
                data["metadata"] = metadata

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            app_logger.info(f"JSON guardado: {path}")
            return True
        except Exception as e:
            app_logger.error(f"Error guardando JSON: {e}")
            return False