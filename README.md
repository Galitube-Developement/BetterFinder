# BetterFinder

BetterFinder is a powerful file search program that enables fast indexing of the file system and provides nearly instant search results.

## Main Features

- Lightning-fast file system indexing
- Instant search results while typing
- Advanced search operators (AND, OR, NOT, wildcards)
- File type filtering
- Search history and file recovery
- Network search for shared drives
- Windows Explorer integration
- Command line support

## Installation

*Installation instructions follow*

## Development

BetterFinder is developed with Python and Qt for the user interface.

## License

See [LICENSE.md](LICENSE.md) for license information.

## Features

- Fast indexing of all files on all hard drives
- Instant search for file names and paths
- Filtering by file extensions
- Search in file contents with the `content:` syntax
- Real-time index updates through NTFS USN Journal
- Dark design with modern user interface

## Requirements

- Windows 10/11
- .NET 6.0 or higher

## Usage

After starting the application, indexing of all hard drives will automatically begin. After indexing is complete, the search bar can be used to quickly search for files.

### Search Functions

- Simple search: Enter part of the file name
- Extension search: Search for files with a specific extension (e.g. ".txt")
- Content search: Use `content:` followed by the search term to search in file contents

## Everything vs. BetterFinder

Like the original Everything, BetterFinder offers:

- Fast indexing of files and folders
- Real-time updates through NTFS USN Journal
- Low resource usage
- Content search for text files

## Performance and Resources

- Fast indexing (few seconds to minutes)
- Low memory usage
- Real-time index updates
- NTFS USN Journal ensures that no changes are missed, even when BetterFinder is not running
