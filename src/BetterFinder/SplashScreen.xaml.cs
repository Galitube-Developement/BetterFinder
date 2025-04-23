using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;
using System.IO;

namespace BetterFinder
{
    public partial class SplashScreen : Window
    {
        private FileIndexer _indexer;
        private List<string> _indexedFiles = new List<string>();
        private bool _indexSystemFiles = false;
        private DateTime _startTime;

        public event EventHandler IndexingCompleted;

        public SplashScreen()
        {
            InitializeComponent();
        }

        public FileIndexer GetFileIndexer()
        {
            return _indexer;
        }

        public async void StartIndexing()
        {
            _startTime = DateTime.Now;
            _indexer = new FileIndexer();
            _indexer.IndexingProgress += Indexer_IndexingProgress;
            _indexer.IndexingComplete += Indexer_IndexingComplete;
            _indexer.IndexSystemFiles = _indexSystemFiles;

            // Starte die Indexierung
            await Task.Run(() => _indexer.StartIndexing());
        }

        private void Indexer_IndexingProgress(object sender, IndexingProgressEventArgs e)
        {
            // UI-Updates müssen im UI-Thread erfolgen
            Dispatcher.Invoke(() =>
            {
                IndexingStatus.Text = $"Indexiere: {e.CurrentFolder}";
                FileCount.Text = $"{e.IndexedFilesCount} Dateien indiziert";
                _indexedFiles = e.IndexedFiles.ToList();
            });
        }

        private void Indexer_IndexingComplete(object sender, EventArgs e)
        {
            // UI-Updates müssen im UI-Thread erfolgen
            Dispatcher.Invoke(() =>
            {
                IndexingStatus.Text = "Indexierung abgeschlossen";
                IndexingProgressBar.IsIndeterminate = false;
                IndexingProgressBar.Value = 100;
                
                // Benachrichtige App über den Abschluss der Indexierung
                IndexingCompleted?.Invoke(this, EventArgs.Empty);
            });
        }

        private void IndexSystemFilesCheckbox_Checked(object sender, RoutedEventArgs e)
        {
            _indexSystemFiles = true;
            if (_indexer != null)
                _indexer.IndexSystemFiles = true;
            
            SystemFilesWarning.Visibility = Visibility.Visible;
        }

        private void IndexSystemFilesCheckbox_Unchecked(object sender, RoutedEventArgs e)
        {
            _indexSystemFiles = false;
            if (_indexer != null)
                _indexer.IndexSystemFiles = false;
            
            SystemFilesWarning.Visibility = Visibility.Collapsed;
        }

        private void StartSearchingButton_Click(object sender, RoutedEventArgs e)
        {
            OpenMainWindow();
        }

        private void OpenMainWindow()
        {
            // Hauptfenster öffnen und indizierte Dateien übergeben
            var mainWindow = new MainWindow(_indexer, _indexedFiles);
            mainWindow.Show();
            
            // Schließe den SplashScreen
            this.Close();
        }
    }
} 