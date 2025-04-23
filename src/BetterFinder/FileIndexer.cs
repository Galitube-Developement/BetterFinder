using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Management;

namespace BetterFinder
{
    public class IndexingStatusEventArgs : EventArgs
    {
        public string Message { get; }
        public string CurrentFolder { get; }

        public IndexingStatusEventArgs(string message, string currentFolder = null)
        {
            Message = message;
            CurrentFolder = currentFolder;
        }
    }

    public class FileIndexer
    {
        private readonly ConcurrentBag<FileInfo> _indexedFiles = new ConcurrentBag<FileInfo>();
        private readonly ConcurrentDictionary<string, List<FileInfo>> _filesByExtension = new ConcurrentDictionary<string, List<FileInfo>>();
        private bool _isIndexing;
        private int _processedFolderCount = 0;
        private readonly object _lockObject = new object();
        private readonly HashSet<string> _excludedFolders = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private readonly ConcurrentDictionary<string, bool> _indexedPaths = new ConcurrentDictionary<string, bool>();
        private CancellationTokenSource _cts;

        // Konfiguration
        private const int MAX_SEARCH_DEPTH = 30;
        private const bool INCLUDE_HIDDEN_SYSTEM_FOLDERS = true;

        // Events
        public event EventHandler<IndexingStatusEventArgs> IndexingStatusChanged;
        public event EventHandler IndexingCompleted;
        public event EventHandler<IndexingProgressEventArgs> IndexingProgress;
        public event EventHandler IndexingComplete;

        // Properties
        public int FileCount => _indexedFiles.Count;
        public bool IsIndexing => _isIndexing;
        public bool IndexSystemFiles { get; set; } = false;

        public FileIndexer()
        {
            // Nur die wichtigsten Ordner ausschließen
            _excludedFolders.Add("$Recycle.Bin");
            _excludedFolders.Add("System Volume Information");
        }

        public void StartIndexing()
        {
            if (_isIndexing)
                return;

            _isIndexing = true;
            _indexedFiles.Clear();
            _filesByExtension.Clear();
            _processedFolderCount = 0;
            _indexedPaths.Clear();
            _cts = new CancellationTokenSource();

            // Start in einem separaten Thread
            Task.Run(() => IndexAllDrives());
        }

        public void StopIndexing()
        {
            if (!_isIndexing)
                return;

            _cts?.Cancel();
            _isIndexing = false;
            OnIndexingStatusChanged("Indexierung wurde vom Benutzer abgebrochen.");
        }

        // KOMPLETT NEUE IMPLEMENTIERUNG DER LAUFWERKSERKENNUNG UND INDEXIERUNG
        private void IndexAllDrives()
        {
            try
            {
                OnIndexingStatusChanged("Starte komplett neue Laufwerks-Indizierung...");
                OnIndexingProgress("Initialisierung", 0);  // Initial Progress-Event

                // 1. BELIEBTE PFADE ZUERST INDEXIEREN
                IndexPopularPaths();
                
                // 2. ALLE VERFÜGBAREN LAUFWERKE MIT MEHREREN METHODEN ERMITTELN
                var availableDrives = GetAllDrivesWithMultipleMethods();
                OnIndexingStatusChanged($"Gefundene Laufwerke: {string.Join(", ", availableDrives)}");
                
                // 3. JEDEN LAUFWERKSBUCHSTABEN EINZELN INDEXIEREN
                foreach (var drive in availableDrives)
                {
                    if (_cts.Token.IsCancellationRequested)
                        break;
                        
                    try
                    {
                        OnIndexingStatusChanged($"Indexiere Laufwerk {drive}...");
                        var rootDir = new DirectoryInfo(drive);
                        IndexDirectoryRecursive(rootDir, 0);
                        OnIndexingStatusChanged($"Laufwerk {drive} erfolgreich indexiert.");
                        
                        // Neue Event für Fortschrittsanzeige auslösen
                        OnIndexingProgress(drive, _indexedFiles.Count);
                    }
                    catch (Exception ex)
                    {
                        OnIndexingStatusChanged($"Fehler beim Indexieren von Laufwerk {drive}: {ex.Message}");
                    }
                }
                
                OnIndexingStatusChanged($"Alle Laufwerke wurden indexiert. {_indexedFiles.Count} Dateien gefunden.");
                OnIndexingProgress("Abgeschlossen", _indexedFiles.Count);  // Finales Progress-Event
                _isIndexing = false;
                OnIndexingCompleted();
            }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Kritischer Fehler bei der Indexierung: {ex.Message}");
                _isIndexing = false;
            }
        }
        
        // Ermittelt alle Laufwerke mit mehreren Methoden für maximale Abdeckung
        private List<string> GetAllDrivesWithMultipleMethods()
        {
            var result = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            
            // METHODE 1: Environment.GetLogicalDrives() - .NET Standard API
            try
            {
                string[] envDrives = Environment.GetLogicalDrives();
                OnIndexingStatusChanged($"Methode 1 (Environment.GetLogicalDrives): {string.Join(", ", envDrives)}");
                foreach (var drive in envDrives)
                {
                    result.Add(drive);
                }
            }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler bei Methode 1: {ex.Message}");
            }
            
            // METHODE 2: DriveInfo.GetDrives() - Systemlaufwerke
            try
            {
                var driveInfos = DriveInfo.GetDrives();
                OnIndexingStatusChanged($"Methode 2 (DriveInfo.GetDrives): {driveInfos.Length} Laufwerke gefunden");
                foreach (var di in driveInfos)
                {
                    result.Add(di.Name);
                    OnIndexingStatusChanged($"Laufwerk gefunden: {di.Name} (Typ: {di.DriveType})");
                }
            }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler bei Methode 2: {ex.Message}");
            }
            
            // METHODE 3: WMI Query - Windows Management Instrumentation
            try
            {
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_LogicalDisk"))
                {
                    var drives = searcher.Get();
                    OnIndexingStatusChanged($"Methode 3 (WMI): {drives.Count} Laufwerke gefunden");
                    
                    foreach (ManagementObject drive in drives)
                    {
                        string driveLetter = drive["DeviceID"].ToString();
                        string description = drive["Description"].ToString();
                        OnIndexingStatusChanged($"WMI Laufwerk: {driveLetter} ({description})");
                        
                        if (!string.IsNullOrEmpty(driveLetter))
                        {
                            if (!driveLetter.EndsWith("\\"))
                                driveLetter += "\\";
                                
                            result.Add(driveLetter);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler bei Methode 3: {ex.Message}");
            }
            
            // METHODE 4: Direkte Pfadprüfung A-Z
            OnIndexingStatusChanged("Methode 4: Direkte Prüfung aller Laufwerksbuchstaben A-Z");
            for (char c = 'A'; c <= 'Z'; c++)
            {
                string path = $"{c}:\\";
                try
                {
                    if (Directory.Exists(path))
                    {
                        result.Add(path);
                        OnIndexingStatusChanged($"Laufwerk {path} existiert");
                    }
                }
                catch
                {
                    // Ignoriere Fehler - manche Pfade werfen Exceptions
                }
            }
            
            // Als Liste zurückgeben
            return result.ToList();
        }
        
        // Indiziert häufig verwendete Pfade zuerst für schnelle Ergebnisse
        private void IndexPopularPaths()
        {
            var popularPaths = new List<string>
            {
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Documents",
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Downloads",
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Desktop",
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Pictures",
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)
            };
            
            OnIndexingStatusChanged("Indexiere häufig verwendete Pfade...");
            
            foreach (var path in popularPaths)
            {
                if (_cts.Token.IsCancellationRequested)
                    break;
                    
                try
                {
                    if (Directory.Exists(path))
                    {
                        OnIndexingStatusChanged($"Indexiere {path}...");
                        IndexDirectoryRecursive(new DirectoryInfo(path), 0);
                    }
                }
                catch (Exception ex)
                {
                    OnIndexingStatusChanged($"Fehler bei {path}: {ex.Message}");
                }
            }
        }
        
        // Einfache rekursive Indizierung eines Verzeichnisses
        private void IndexDirectoryRecursive(DirectoryInfo directory, int depth)
        {
            if (_cts.Token.IsCancellationRequested || depth > MAX_SEARCH_DEPTH)
                return;
                
            // Bereits besuchte Pfade überspringen
            if (_indexedPaths.ContainsKey(directory.FullName))
                return;
                
            _indexedPaths.TryAdd(directory.FullName, true);
            
            // Prüfe, ob der Ordner ausgeschlossen werden soll
            if (ShouldExcludeDirectory(directory))
                return;

            // Statusaktualisierung (nicht zu oft, um Performance zu erhalten)
            if (Interlocked.Increment(ref _processedFolderCount) % 10 == 0)
            {
                OnIndexingStatusChanged($"{_indexedFiles.Count} Dateien, {_processedFolderCount} Ordner", 
                    directory.FullName);
                // Fortschritt auch an den SplashScreen melden
                OnIndexingProgress(directory.FullName, _indexedFiles.Count);
            }

            // Dateien im aktuellen Verzeichnis
            try
            {
                ProcessFiles(directory.GetFiles());
                
                // Nach jeder Verzeichnisverarbeitung den Fortschritt melden
                if (_indexedFiles.Count % 50 == 0)
                {
                    OnIndexingProgress(directory.FullName, _indexedFiles.Count);
                }
            }
            catch (UnauthorizedAccessException) { }
            catch (IOException) { }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler beim Lesen von Dateien in {directory.FullName}: {ex.Message}");
            }

            // Unterverzeichnisse
            try
            {
                foreach (var subDir in directory.GetDirectories())
                {
                    if (_cts.Token.IsCancellationRequested)
                        break;
                        
                    IndexDirectoryRecursive(subDir, depth + 1);
                }
            }
            catch (UnauthorizedAccessException) { }
            catch (IOException) { }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler beim Lesen von Unterverzeichnissen in {directory.FullName}: {ex.Message}");
            }
        }

        private bool ShouldExcludeDirectory(DirectoryInfo directory)
        {
            // Ausgeschlossene Ordnernamen (z.B. Recycle Bin)
            if (_excludedFolders.Contains(directory.Name))
                return true;
            
            // Versteckte oder Systemordner optional ausschließen
            if (!INCLUDE_HIDDEN_SYSTEM_FOLDERS)
            {
                try
                {
                    if ((directory.Attributes & FileAttributes.Hidden) == FileAttributes.Hidden || 
                        (directory.Attributes & FileAttributes.System) == FileAttributes.System)
                    {
                        return true;
                    }
                }
                catch { }
            }

            return false;
        }

        private void ProcessFiles(FileInfo[] files)
        {
            if (files == null || files.Length == 0)
                return;

            int counter = 0;
            foreach (var file in files)
            {
                _indexedFiles.Add(file);
                counter++;

                string ext = file.Extension.ToLowerInvariant();
                _filesByExtension.AddOrUpdate(
                    ext,
                    new List<FileInfo> { file },
                    (_, existingList) =>
                    {
                        lock (_lockObject)
                        {
                            existingList.Add(file);
                            return existingList;
                        }
                    }
                );
                
                // Regelmäßig den Fortschritt melden (nach jeweils 20 Dateien)
                if (counter % 20 == 0)
                {
                    OnIndexingProgress(file.DirectoryName, _indexedFiles.Count);
                }
            }
            
            // Nach jeder Verarbeitungsgruppe den Fortschritt melden
            if (files.Length > 0)
            {
                OnIndexingProgress(files[0].DirectoryName, _indexedFiles.Count);
            }
        }

        public IEnumerable<FileInfo> Search(string searchTerm)
        {
            if (string.IsNullOrWhiteSpace(searchTerm))
                return Enumerable.Empty<FileInfo>();

            searchTerm = searchTerm.ToLowerInvariant().Trim();

            // Suche nach Dateinamen oder Pfad
            var results = _indexedFiles.Where(f => 
                f.Name.ToLowerInvariant().Contains(searchTerm) || 
                Path.GetFileNameWithoutExtension(f.Name).ToLowerInvariant().Contains(searchTerm) ||
                f.FullName.ToLowerInvariant().Contains(searchTerm));

            // Nach Dateierweiterung suchen (z.B. ".txt")
            if (searchTerm.StartsWith("."))
            {
                if (_filesByExtension.TryGetValue(searchTerm, out var filesByExt))
                {
                    results = results.Union(filesByExt);
                }
            }

            return results.OrderBy(f => f.Name);
        }

        protected virtual void OnIndexingStatusChanged(string message, string currentFolder = null)
        {
            IndexingStatusChanged?.Invoke(this, new IndexingStatusEventArgs(message, currentFolder));
        }

        protected virtual void OnIndexingCompleted()
        {
            IndexingCompleted?.Invoke(this, EventArgs.Empty);
            
            // Neues Event für die Indexierung abgeschlossen
            IndexingComplete?.Invoke(this, EventArgs.Empty);
        }
        
        protected virtual void OnIndexingProgress(string currentFolder, int indexedFilesCount)
        {
            var args = new IndexingProgressEventArgs(
                currentFolder,
                indexedFilesCount,
                _indexedFiles.Select(f => f.FullName).ToList()
            );
            
            IndexingProgress?.Invoke(this, args);
        }
    }
    
    // Neue Klasse für die Fortschrittsmeldung
    public class IndexingProgressEventArgs : EventArgs
    {
        public string CurrentFolder { get; }
        public int IndexedFilesCount { get; }
        public IReadOnlyList<string> IndexedFiles { get; }
        
        public IndexingProgressEventArgs(string currentFolder, int indexedFilesCount, List<string> indexedFiles)
        {
            CurrentFolder = currentFolder;
            IndexedFilesCount = indexedFilesCount;
            IndexedFiles = indexedFiles;
        }
    }
} 