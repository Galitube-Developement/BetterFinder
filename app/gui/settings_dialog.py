    def save_settings(self):
        """Speichert die Einstellungen und schließt den Dialog."""
        try:
            # Speichere Hotkey
            settings.set_setting("hotkey", self.hotkey_edit.text())
            
            # Speichere Autostart-Einstellung
            autostart = self.autostart_checkbox.isChecked()
            settings.set_setting("autostart", autostart)
            
            # Autostart konfigurieren
            try:
                self.main_window.setup_autostart(autostart)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Autostart-Fehler",
                    f"Einstellungen wurden gespeichert, aber der Autostart konnte nicht konfiguriert werden:\n\n{str(e)}\n\n"
                    "Mögliche Lösungen:\n"
                    "- Programm als Administrator starten\n"
                    "- Prüfen Sie die Berechtigungen für den Autostart-Ordner\n"
                    "- Deaktivieren Sie die Autostart-Option"
                )
                # Setze Autostart-Einstellung zurück
                settings.set_setting("autostart", False)
                self.autostart_checkbox.setChecked(False)
            
            # Speichere ausgeschlossene Pfade
            paths = []
            for i in range(self.excluded_paths_list.count()):
                paths.append(self.excluded_paths_list.item(i).text())
            settings.set_setting("excluded_paths", paths)
            
            # Speichere maximale Ergebnisse
            settings.set_setting("max_results", self.max_results_spinbox.value())
            
            # Schreibe Einstellungen in die Datei
            settings.save_settings()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Speichern",
                f"Die Einstellungen konnten nicht gespeichert werden:\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc() 