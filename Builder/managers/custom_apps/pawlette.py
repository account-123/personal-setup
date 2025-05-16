import ast
import json
import subprocess
import traceback

from loguru import logger

from .base import AppConfigurer


class PawletteConfigurer(AppConfigurer):
    def setup(self) -> None:
        try:
            self._install_available_themes()
        except Exception:
            logger.error(f"Pawlette main setup error: {traceback.format_exc()}")

    def _parse_themes(self, raw: str) -> dict:
        """Пытается распарсить вывод разными способами"""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed JSON parse, trying literal eval")
            try:
                data = ast.literal_eval(raw)
                if isinstance(data, dict):
                    return data
                raise ValueError("Not a dictionary")
            except Exception:
                logger.error("All parsing attempts failed")
                raise

    def _install_available_themes(self) -> None:
        error_msg = "Theme data parsing failed: {err}"
        try:
            result = subprocess.run(
                ["pawlette", "get-available-themes"],
                capture_output=True,
                text=True,
                check=True,
            )

            try:
                themes = self._parse_themes(result.stdout.strip())
            except Exception:
                logger.error(traceback.format_exc())
                raise

            if not isinstance(themes, dict):
                raise ValueError("Expected dictionary of themes")

            error_msg = "Skipping theme {theme_name}: {err}"
            for theme_name in themes:
                try:
                    self._install_theme(theme_name)
                except subprocess.CalledProcessError as e:
                    logger.error(error_msg.format(theme_name=theme_name, err=e.stderr))
                except Exception:
                    logger.error(
                        error_msg.format(
                            theme_name=theme_name, err=traceback.format_exc()
                        )
                    )
                    continue
        except subprocess.CalledProcessError as e:
            logger.error(error_msg.format(err=e.stderr))
        except Exception:
            logger.error(error_msg.format(err=traceback.format_exc()))

    def _install_theme(self, theme_name: str) -> None:
        """Логика установки темы без изменений"""
        logger.info(f"Installing theme: {theme_name}")
        subprocess.run(
            ["pawlette", "install-theme", theme_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.success(f"Theme {theme_name} installed")
