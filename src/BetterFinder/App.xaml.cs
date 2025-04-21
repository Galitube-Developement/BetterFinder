using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

namespace BetterFinder
{
    public partial class App : Application
    {
        private SplashScreen _splashScreen;
        
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            
            // Erstelle und zeige den Splash Screen
            _splashScreen = new SplashScreen();
            _splashScreen.Show();
            
            // Registriere das Event für den Abschluss der Indexierung
            _splashScreen.IndexingCompleted += SplashScreen_IndexingCompleted;
            
            // Starte die Indexierung
            _splashScreen.StartIndexing();
        }
        
        private void SplashScreen_IndexingCompleted(object sender, EventArgs e)
        {
            // Verzögerung hinzufügen, damit der Benutzer den abgeschlossenen Status sehen kann
            Task.Delay(1000).ContinueWith(_ =>
            {
                Dispatcher.Invoke(() =>
                {
                    // Hole den FileIndexer vom Splash Screen
                    var fileIndexer = _splashScreen.GetFileIndexer();
                    
                    // Erstelle und öffne das Hauptfenster
                    var mainWindow = new MainWindow(fileIndexer);
                    mainWindow.Show();
                    
                    // Schließe den Splash Screen
                    _splashScreen.Close();
                    _splashScreen = null;
                });
            });
        }
    }
} 