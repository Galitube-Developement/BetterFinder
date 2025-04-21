using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace BetterFinder
{
    public class IndexingStatusEventArgs : EventArgs
    {
        public string Message { get; }
        public string CurrentFolder { get; } // Aktueller Ordner, der indiziert wird

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

        // Erhöhte Anzahl der parallelen Tasks für die Indizierung
        private const int MaxParallelTasks = 16;
        
        // Maximal zu durchsuchende Tiefe (nur für bestimmte Pfade)
        private const int MaxDepthForNonSystemDrives = 6;

        public event EventHandler<IndexingStatusEventArgs> IndexingStatusChanged;
        public event EventHandler IndexingCompleted;

        public int FileCount => _indexedFiles.Count;

        public bool IsIndexing => _isIndexing;
        
        // Option zum vollständigen Indizieren
        public bool IndexEverything { get; set; } = false;

        public FileIndexer()
        {
            // Mehr Ordner ausschließen für bessere Performance
            _excludedFolders.Add("$Recycle.Bin");
            _excludedFolders.Add("System Volume Information");
            _excludedFolders.Add("tmp");
            _excludedFolders.Add("temp");
            _excludedFolders.Add("cache");
            _excludedFolders.Add("node_modules");
            _excludedFolders.Add(".git");
            _excludedFolders.Add("bower_components");
            _excludedFolders.Add("vendor");
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

            Task.Run(() => IndexDrives());
        }

        private void IndexDrives()
        {
            try
            {
                // Oft genutzte Pfade priorisieren für schnellere Ergebnisse
                List<string> priorityPaths = new List<string>
                {
                    $"{Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)}\\Documents",
                    $"{Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)}\\Downloads",
                    $"{Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)}\\Desktop",
                    $"{Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)}\\Pictures",
                    $"{Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)}"
                };
                
                // Zuerst wichtige Pfade indexieren
                OnIndexingStatusChanged("Indexiere wichtige Pfade...");
                Parallel.ForEach(priorityPaths, new ParallelOptions { MaxDegreeOfParallelism = MaxParallelTasks }, path =>
                {
                    try 
                    {
                        if (Directory.Exists(path))
                        {
                            OnIndexingStatusChanged($"Indexiere {path}...");
                            IndexDirectory(new DirectoryInfo(path), 0, true);
                        }
                    }
                    catch (Exception ex)
                    {
                        OnIndexingStatusChanged($"Fehler bei Indexierung von {path}: {ex.Message}");
                    }
                });

                List<string> drives = new List<string>();
                
                // Alle möglichen Laufwerksbuchstaben C-Z durchgehen (C zuerst)
                drives.Add("C:\\");
                for (char driveLetter = 'D'; driveLetter <= 'Z'; driveLetter++)
                {
                    string drivePath = $"{driveLetter}:\\";
                    try
                    {
                        // Prüfen ob Laufwerk existiert
                        if (Directory.Exists(drivePath))
                        {
                            drives.Add(drivePath);
                            OnIndexingStatusChanged($"Laufwerk {drivePath} gefunden und wird indexiert.");
                        }
                    }
                    catch (Exception ex)
                    {
                        // Ignoriere Fehler beim Prüfen und fahre mit dem nächsten Laufwerk fort
                        OnIndexingStatusChanged($"Laufwerk {drivePath} konnte nicht geprüft werden: {ex.Message}");
                    }
                }
                
                OnIndexingStatusChanged($"Gefundene Laufwerke: {string.Join(", ", drives)}");
                
                // C: zuerst indexieren, mit voller Tiefe
                if (drives.Contains("C:\\"))
                {
                    OnIndexingStatusChanged("Indexiere C:\\...");
                    IndexDirectory(new DirectoryInfo("C:\\"), 0, true);
                    drives.Remove("C:\\");
                }
                
                // Andere Laufwerke parallel indexieren mit begrenzter Tiefe
                if (drives.Count > 0)
                {
                    OnIndexingStatusChanged($"Indexiere {drives.Count} weitere Laufwerke...");
                    Parallel.ForEach(drives, new ParallelOptions { MaxDegreeOfParallelism = MaxParallelTasks }, drive =>
                    {
                        try 
                        {
                            OnIndexingStatusChanged($"Indexiere Laufwerk {drive}...");
                            IndexDirectory(new DirectoryInfo(drive), 0, false); // Begrenzte Tiefe für andere Laufwerke
                        }
                        catch (Exception ex)
                        {
                            OnIndexingStatusChanged($"Fehler bei Indexierung von {drive}: {ex.Message}");
                        }
                    });
                }

                _isIndexing = false;
                OnIndexingCompleted();
            }
            catch (Exception ex)
            {
                OnIndexingStatusChanged($"Fehler bei der Indexierung: {ex.Message}");
                _isIndexing = false;
            }
        }

        private string GetDriveTypeDescription(DriveType driveType)
        {
            switch (driveType)
            {
                case DriveType.Fixed:
                    return "Festplatten";
                case DriveType.Removable:
                    return "Wechseldatenträger";
                case DriveType.Network:
                    return "Netzwerk";
                case DriveType.CDRom:
                    return "CD/DVD";
                case DriveType.Ram:
                    return "RAM-Disk";
                default:
                    return driveType.ToString();
            }
        }

        private void IndexDirectory(DirectoryInfo directory, int currentDepth = 0, bool isFullIndexing = true)
        {
            try
            {
                // Bereits indexierte Pfade überspringen
                if (_indexedPaths.ContainsKey(directory.FullName))
                    return;
                    
                _indexedPaths.TryAdd(directory.FullName, true);
                
                // Tiefenbegrenzung für nicht-priorisierte Laufwerke
                if (!isFullIndexing && currentDepth > MaxDepthForNonSystemDrives)
                    return;
                
                // Überprüfe, ob der Ordner ausgeschlossen werden soll
                if (ShouldExcludeDirectory(directory))
                    return;

                // Status aktualisieren mit aktuellem Ordner
                if (_processedFolderCount % 20 == 0) // Nur gelegentlich aktualisieren, um Performance zu erhalten
                {
                    OnIndexingStatusChanged($"{_indexedFiles.Count} Dateien indiziert, {_processedFolderCount} Ordner verarbeitet...", 
                        directory.FullName);
                }

                // Dateien im aktuellen Verzeichnis
                FileInfo[] files = null;
                try
                {
                    files = directory.GetFiles();
                    ProcessFiles(files);

                    // Status-Update alle 500 verarbeiteten Ordner
                    Interlocked.Increment(ref _processedFolderCount);
                    if (_processedFolderCount % 500 == 0)
                    {
                        OnIndexingStatusChanged($"{_indexedFiles.Count} Dateien indiziert, {_processedFolderCount} Ordner verarbeitet...");
                    }
                }
                catch (UnauthorizedAccessException) { }
                catch (IOException) { }

                // Unterverzeichnisse
                DirectoryInfo[] subDirs = null;
                try
                {
                    subDirs = directory.GetDirectories();
                }
                catch (UnauthorizedAccessException) { }
                catch (IOException) { }

                if (subDirs != null && subDirs.Length > 0)
                {
                    // Verarbeite Unterverzeichnisse parallel bei großen Ordnern
                    if (subDirs.Length > 10)
                    {
                        Parallel.ForEach(subDirs, new ParallelOptions { MaxDegreeOfParallelism = MaxParallelTasks }, subDir =>
                        {
                            IndexDirectory(subDir, currentDepth + 1, isFullIndexing);
                        });
                    }
                    else
                    {
                        foreach (DirectoryInfo subDir in subDirs)
                        {
                            IndexDirectory(subDir, currentDepth + 1, isFullIndexing);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                // Fehler nur für die wichtigsten Pfade loggen
                if (directory.FullName.StartsWith("C:\\"))
                {
                    OnIndexingStatusChanged($"Fehler beim Indexieren von {directory.FullName}: {ex.Message}");
                }
            }
        }

        private bool ShouldExcludeDirectory(DirectoryInfo directory)
        {
            if (IndexEverything && !_excludedFolders.Contains(directory.Name))
                return false;
            
            // Name-basierte Ausschlüsse
            if (_excludedFolders.Contains(directory.Name))
                return true;
            
            // Versteckte oder Systemordner überspringen
            try
            {
                if (!IndexEverything && 
                    ((directory.Attributes & FileAttributes.Hidden) == FileAttributes.Hidden || 
                    (directory.Attributes & FileAttributes.System) == FileAttributes.System))
                {
                    return true;
                }
            }
            catch { }

            return false;
        }

        private void ProcessFiles(FileInfo[] files)
        {
            if (files == null || files.Length == 0)
                return;

            foreach (var file in files)
            {
                _indexedFiles.Add(file);

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
            }
        }

        public IEnumerable<FileInfo> Search(string searchTerm)
        {
            if (string.IsNullOrWhiteSpace(searchTerm))
                return Enumerable.Empty<FileInfo>();

            searchTerm = searchTerm.ToLowerInvariant();

            // Suche nach Dateinamen
            var results = _indexedFiles.Where(f => 
                f.Name.ToLowerInvariant().Contains(searchTerm) || 
                f.FullName.ToLowerInvariant().Contains(searchTerm));

            // Berücksichtige Dateierweiterungen
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
        }
    }
} 