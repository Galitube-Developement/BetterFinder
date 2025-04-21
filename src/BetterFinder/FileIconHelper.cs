using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media.Imaging;

namespace BetterFinder
{
    public static class FileIconHelper
    {
        [DllImport("shell32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr SHGetFileInfo(string pszPath, uint dwFileAttributes, ref SHFILEINFO psfi, uint cbSizeFileInfo, uint uFlags);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private struct SHFILEINFO
        {
            public IntPtr hIcon;
            public int iIcon;
            public uint dwAttributes;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
            public string szDisplayName;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 80)]
            public string szTypeName;
        }

        private const uint SHGFI_ICON = 0x100;
        private const uint SHGFI_SMALLICON = 0x1;
        private const uint SHGFI_LARGEICON = 0x0;
        private const uint FILE_ATTRIBUTE_NORMAL = 0x80;

        private static readonly Cache<string, BitmapSource> _iconCache = new Cache<string, BitmapSource>(500);

        public static BitmapSource GetFileIcon(string filePath, bool smallIcon = true)
        {
            if (string.IsNullOrEmpty(filePath))
                return null;

            // Verwende den Cache
            string cacheKey = filePath + (smallIcon ? "_small" : "_large");
            if (_iconCache.TryGet(cacheKey, out var cachedIcon))
                return cachedIcon;

            try
            {
                SHFILEINFO info = new SHFILEINFO();
                uint flags = SHGFI_ICON | (smallIcon ? SHGFI_SMALLICON : SHGFI_LARGEICON);

                SHGetFileInfo(filePath, FILE_ATTRIBUTE_NORMAL, ref info, (uint)Marshal.SizeOf(info), flags);

                if (info.hIcon == IntPtr.Zero)
                    return null;

                var icon = Icon.FromHandle(info.hIcon);
                BitmapSource bitmapSource = Imaging.CreateBitmapSourceFromHIcon(
                    icon.Handle,
                    Int32Rect.Empty,
                    BitmapSizeOptions.FromEmptyOptions());

                // Icon-Handle freigeben
                DestroyIcon(info.hIcon);

                // Ergebnis im Cache speichern
                _iconCache.Add(cacheKey, bitmapSource);

                return bitmapSource;
            }
            catch
            {
                return null;
            }
        }

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool DestroyIcon(IntPtr hIcon);
    }

    public class Cache<TKey, TValue>
    {
        private readonly Dictionary<TKey, TValue> _cache = new Dictionary<TKey, TValue>();
        private readonly Queue<TKey> _cacheOrder = new Queue<TKey>();
        private readonly int _maxItems;

        public Cache(int maxItems)
        {
            _maxItems = maxItems;
        }

        public bool TryGet(TKey key, out TValue value)
        {
            lock (_cache)
            {
                return _cache.TryGetValue(key, out value);
            }
        }

        public void Add(TKey key, TValue value)
        {
            lock (_cache)
            {
                if (_cache.ContainsKey(key))
                    return;

                if (_cache.Count >= _maxItems)
                {
                    // Ältesten Eintrag entfernen
                    var oldestKey = _cacheOrder.Dequeue();
                    _cache.Remove(oldestKey);
                }

                _cache[key] = value;
                _cacheOrder.Enqueue(key);
            }
        }
    }
} 