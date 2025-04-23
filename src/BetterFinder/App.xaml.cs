using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Forms;
using System.Windows.Media;
using Hardcodet.Wpf.TaskbarNotification;
using System.IO;

namespace BetterFinder
{
    public partial class App : System.Windows.Application
    {
        private SplashScreen _splashScreen;
        private MainWindow _mainWindow;
        private TaskbarIcon _notifyIcon;
        private FileIndexer _fileIndexer;
        
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
            
            // Initialisiere Tray-Icon
            InitializeTrayIcon();
        }
        
        private void SplashScreen_IndexingCompleted(object sender, EventArgs e)
        {
            // Verzögerung hinzufügen, damit der Benutzer den abgeschlossenen Status sehen kann
            Task.Delay(1000).ContinueWith(_ =>
            {
                Dispatcher.Invoke(() =>
                {
                    // Hole den FileIndexer vom Splash Screen
                    _fileIndexer = _splashScreen.GetFileIndexer();
                    
                    // Erstelle und öffne das Hauptfenster
                    _mainWindow = new MainWindow(_fileIndexer);
                    _mainWindow.Show();
                    
                    // Schließe den Splash Screen
                    _splashScreen.Close();
                    _splashScreen = null;
                    
                    // WICHTIG: Verbinde das Schließen-Ereignis vom Hauptfenster
                    // HINWEIS: In MainWindow ist bereits ein eigener Handler hinzugefügt worden,
                    // daher wird er hier nicht mehr benötigt
                    // _mainWindow.Closing += MainWindow_Closing;
                });
            });
        }
        
        private void InitializeTrayIcon()
        {
            _notifyIcon = new TaskbarIcon();
            
            // Einfacherer Ansatz: Erstelle ein Standard-Icon für das Tray
            using (var stream = new System.IO.MemoryStream())
            {
                var bitmap = new System.Drawing.Bitmap(16, 16);
                using (var g = System.Drawing.Graphics.FromImage(bitmap))
                {
                    g.Clear(System.Drawing.Color.DodgerBlue);
                    g.DrawString("BF", new System.Drawing.Font("Arial", 8), 
                        System.Drawing.Brushes.White, 0, 0);
                }
                bitmap.Save(stream, System.Drawing.Imaging.ImageFormat.Png);
                
                var icon = System.Drawing.Icon.FromHandle(bitmap.GetHicon());
                _notifyIcon.Icon = icon;
            }
            
            _notifyIcon.ToolTipText = "BetterFinder";
            
            // Verhindern, dass das Standardmenü angezeigt wird, indem wir dem Windows-API-Event zuvor kommen
            _notifyIcon.TrayRightMouseUp += (sender, args) => 
            {
                // Wird aufgerufen, wenn das rechte Maustaste losgelassen wird
                System.Diagnostics.Debug.WriteLine("TrayRightMouseUp - Showing custom context menu");
                args.Handled = true;
                
                // Zeige unser eigenes Kontextmenü beim Release, was zuverlässiger ist
                var menu = CreateTrayContextMenu();
                menu.IsOpen = true;
            };
            
            // Eigene Behandlung des rechten Mausklicks
            _notifyIcon.TrayRightMouseDown += (sender, args) =>
            {
                System.Diagnostics.Debug.WriteLine("TrayRightMouseDown - Blocking default context menu");
                // Nur das Standardverhalten blockieren, aber nicht selbst das Menu öffnen
                args.Handled = true;
            };
            
            // Ereignisbehandlung für Doppelklick auf das Tray-Icon
            _notifyIcon.TrayMouseDoubleClick += (sender, args) =>
            {
                System.Diagnostics.Debug.WriteLine("TrayMouseDoubleClick");
                ShowMainWindow();
            };
            
            // Erstelle das Kontextmenü mit WPF ContextMenu
            var menu = CreateTrayContextMenu();
            // Stelle sicher, dass es dem TaskbarIcon zugewiesen wird
            _notifyIcon.ContextMenu = menu;
        }
        
        private System.Windows.Controls.ContextMenu CreateTrayContextMenu()
        {
            // Neues Kontextmenü erstellen
            var menu = new System.Windows.Controls.ContextMenu();
            
            // Öffnen-Menüpunkt
            var openItem = new System.Windows.Controls.MenuItem { Header = "Öffnen" };
            openItem.Click += (sender, args) => 
            {
                System.Diagnostics.Debug.WriteLine("Open clicked");
                ShowMainWindow();
            };
            menu.Items.Add(openItem);
            
            // Neu indexieren-Menüpunkt
            var reindexItem = new System.Windows.Controls.MenuItem { Header = "Neu indexieren" };
            reindexItem.Click += (sender, args) => 
            {
                System.Diagnostics.Debug.WriteLine("Reindex clicked");
                ReindexFiles();
            };
            menu.Items.Add(reindexItem);
            
            // Trennlinie
            menu.Items.Add(new System.Windows.Controls.Separator());
            
            // Beenden-Menüpunkt
            var exitItem = new System.Windows.Controls.MenuItem { Header = "Beenden" };
            exitItem.Click += (sender, args) => 
            {
                System.Diagnostics.Debug.WriteLine("Exit clicked");
                ExitApplication();
            };
            menu.Items.Add(exitItem);
            
            return menu;
        }
        
        private void ShowMainWindow()
        {
            System.Diagnostics.Debug.WriteLine("ShowMainWindow called");
            
            if (_mainWindow == null)
            {
                // Falls das Hauptfenster noch nicht erstellt wurde
                // Erstelle es neu, wenn es benötigt wird
                System.Diagnostics.Debug.WriteLine("_mainWindow is null, creating new window");
                if (_fileIndexer != null)
                {
                    _mainWindow = new MainWindow(_fileIndexer);
                    _mainWindow.Closed += (s, e) => _mainWindow = null; // Aufräumen bei Schließen
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("Cannot create window, _fileIndexer is null");
                    return;
                }
            }
            
            // Zeige das Hauptfenster an und bringe es in den Vordergrund
            System.Diagnostics.Debug.WriteLine("Showing main window");
            _mainWindow.Show();
            _mainWindow.WindowState = WindowState.Normal;
            _mainWindow.Activate();
        }
        
        private void ReindexFiles()
        {
            System.Diagnostics.Debug.WriteLine("ReindexFiles called");
            
            if (_fileIndexer != null)
            {
                System.Diagnostics.Debug.WriteLine("Starting indexing");
                _fileIndexer.StartIndexing();
                
                // Wenn das Hauptfenster geöffnet ist, aktualisiere den Status
                if (_mainWindow != null && _mainWindow.IsVisible)
                {
                    System.Diagnostics.Debug.WriteLine("Showing indexing status in main window");
                    _mainWindow.ShowIndexingStatus();
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("Main window not visible or null");
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine("Cannot reindex, _fileIndexer is null");
            }
        }
        
        private void ExitApplication()
        {
            // Cleanup für Tray-Icon
            _notifyIcon.Dispose();
            
            // Beende die Anwendung
            Current.Shutdown();
        }
    }
} 