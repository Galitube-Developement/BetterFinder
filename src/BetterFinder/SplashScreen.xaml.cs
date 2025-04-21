using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace BetterFinder
{
    public partial class SplashScreen : Window
    {
        private FileIndexer _fileIndexer;
        public event EventHandler IndexingCompleted;
        private DateTime _startTime;

        public SplashScreen()
        {
            InitializeComponent();
        }

        public void StartIndexing()
        {
            _startTime = DateTime.Now;
            _fileIndexer = new FileIndexer();
            
            // Setze die IndexEverything-Eigenschaft basierend auf der Checkbox
            _fileIndexer.IndexEverything = IndexEverythingCheckbox.IsChecked ?? false;
            
            _fileIndexer.IndexingStatusChanged += (s, e) =>
            {
                Dispatcher.Invoke(() =>
                {
                    StatusText.Text = e.Message;
                    
                    if (e.Message.StartsWith("Indiziere"))
                    {
                        CurrentDriveText.Text = e.Message;
                    }
                    else if (e.Message.Contains("Dateien indiziert"))
                    {
                        FileCountText.Text = e.Message;
                    }
                    
                    // Aktuellen Ordner anzeigen, wenn verfügbar
                    if (!string.IsNullOrEmpty(e.CurrentFolder))
                    {
                        CurrentFolderText.Text = $"Aktueller Ordner: {e.CurrentFolder}";
                    }
                });
            };

            _fileIndexer.IndexingCompleted += (s, e) =>
            {
                Dispatcher.Invoke(() =>
                {
                    var timeElapsed = DateTime.Now - _startTime;
                    StatusText.Text = "Indizierung abgeschlossen";
                    
                    // Zeige die Gesamtzahl der indizierten Dateien und die verstrichene Zeit an
                    FileCountText.Text = $"{_fileIndexer.FileCount:N0} Dateien in {timeElapsed.TotalSeconds:N1} Sekunden indiziert";
                    
                    // Fortschrittsanzeige auf 100% setzen
                    IndexingProgress.IsIndeterminate = false;
                    IndexingProgress.Value = 100;
                    IndexingProgress.Foreground = new SolidColorBrush(Colors.LimeGreen);
                    
                    // Fortschrittsbalken pulsieren lassen
                    var animation = new ColorAnimation();
                    animation.From = Colors.LimeGreen;
                    animation.To = Color.FromRgb(0, 120, 215); // #0078D7
                    animation.Duration = TimeSpan.FromSeconds(0.8);
                    animation.AutoReverse = true;
                    animation.RepeatBehavior = RepeatBehavior.Forever;
                    
                    IndexingProgress.Foreground.BeginAnimation(SolidColorBrush.ColorProperty, animation);
                    
                    // Löst das Event aus, das signalisiert, dass die Indexierung abgeschlossen ist
                    IndexingCompleted?.Invoke(this, EventArgs.Empty);
                });
            };

            // Starte die Indexierung
            _fileIndexer.StartIndexing();
        }

        public FileIndexer GetFileIndexer()
        {
            return _fileIndexer;
        }
        
        private void IndexEverythingCheckbox_Checked(object sender, RoutedEventArgs e)
        {
            // Zeige Warnung, dass dies länger dauern kann
            MessageBox.Show(
                "Achtung: Bei Aktivierung dieser Option werden auch System- und versteckte Ordner indexiert. " +
                "Dies kann deutlich länger dauern und mehr Speicher benötigen.", 
                "Vollständige Indexierung", 
                MessageBoxButton.OK, 
                MessageBoxImage.Information);
        }
        
        private void IndexEverythingCheckbox_Unchecked(object sender, RoutedEventArgs e)
        {
            // Nichts zu tun bei Deaktivierung
        }
    }
} 