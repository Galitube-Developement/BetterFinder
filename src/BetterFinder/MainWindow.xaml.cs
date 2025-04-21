using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace BetterFinder
{
    public partial class MainWindow : Window
    {
        private ObservableCollection<FileItem> _fileItems;
        private FileIndexer _fileIndexer;
        private const int MaxFilesToShow = 10; // Maximal 10 Dateien anzeigen
        private double _baseHeight;
        private double _itemHeight = 30; // Ungefähre Höhe eines ListView-Items
        private DispatcherTimer _searchTimer; // Timer für verzögerte Suche

        public MainWindow(FileIndexer fileIndexer)
        {
            InitializeComponent();

            _fileItems = new ObservableCollection<FileItem>();
            FileListView.ItemsSource = _fileItems;

            // Basisgröße des Fensters speichern
            _baseHeight = this.Height;

            // Initialisiere den Timer für verzögerte Suche
            _searchTimer = new DispatcherTimer();
            _searchTimer.Interval = TimeSpan.FromMilliseconds(300); // 300ms Verzögerung
            _searchTimer.Tick += SearchTimer_Tick;

            // Verwende den bereits initialisierten FileIndexer
            _fileIndexer = fileIndexer;
            
            // Setze den Fokus auf das Suchfeld
            Loaded += (s, e) => 
            {
                SearchBox.Focus();
                StatusText.Text = $"Bereit - {_fileIndexer.FileCount} Dateien indexiert";
            };
        }

        private void SearchTimer_Tick(object sender, EventArgs e)
        {
            _searchTimer.Stop();
            PerformSearch(SearchBox.Text);
        }

        private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            // Platzhaltertext ein-/ausblenden basierend auf dem Inhalt der TextBox
            if (string.IsNullOrEmpty(SearchBox.Text))
            {
                PlaceholderText.Visibility = Visibility.Visible;
                _fileItems.Clear(); // Liste leeren, wenn Suchfeld leer ist
                ResizeWindowBasedOnResults(0);
            }
            else
            {
                PlaceholderText.Visibility = Visibility.Collapsed;
                
                // Starte den Timer neu, um die Suche mit Verzögerung auszuführen
                // (verhindert zu viele Suchanfragen während des Tippens)
                _searchTimer.Stop();
                _searchTimer.Start();
            }
        }

        private void SearchBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                _searchTimer.Stop(); // Timer stoppen, wenn Enter gedrückt wird
                PerformSearch(SearchBox.Text);
            }
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                Close();
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void PerformSearch(string searchTerm)
        {
            if (string.IsNullOrWhiteSpace(searchTerm))
            {
                return;
            }

            StatusText.Text = "Suche...";
            _fileItems.Clear();

            var results = _fileIndexer.Search(searchTerm);
            var limitedResults = results.Take(MaxFilesToShow); // Begrenze auf maximal 10 Ergebnisse
            
            foreach (var file in limitedResults)
            {
                var icon = GetFileIcon(file.FullName);
                _fileItems.Add(new FileItem
                {
                    Name = file.Name,
                    Path = file.FullName,
                    Icon = icon
                });
            }

            // Smart Sizing des Fensters basierend auf der Anzahl der Ergebnisse
            ResizeWindowBasedOnResults(_fileItems.Count);

            StatusText.Text = $"{_fileItems.Count} Ergebnisse für \"{searchTerm}\"";
        }

        private void ResizeWindowBasedOnResults(int resultCount)
        {
            if (resultCount == 0)
            {
                // Minimale Höhe wenn keine Ergebnisse
                this.Height = _baseHeight - 100;
            }
            else
            {
                // Passe die Höhe basierend auf der Anzahl der Ergebnisse an
                // Aber begrenzt auf maximal die Originalhöhe
                double newHeight = _baseHeight - 100 + (resultCount * _itemHeight);
                this.Height = Math.Min(newHeight, _baseHeight);
            }
        }

        private BitmapSource GetFileIcon(string filePath)
        {
            return FileIconHelper.GetFileIcon(filePath, true);
        }

        private void FileListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (FileListView.SelectedItem is FileItem selectedItem)
            {
                try
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = selectedItem.Path,
                        UseShellExecute = true
                    });

                    // Schließe das Programm nachdem eine Datei ausgewählt wurde
                    Close();
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Fehler beim Öffnen der Datei: {ex.Message}", "Fehler", 
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }
    }

    public class FileItem
    {
        public string Name { get; set; }
        public string Path { get; set; }
        public BitmapSource Icon { get; set; }
    }
} 