# EP PyDICOM Anonymizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub Releases](https://img.shields.io/github/v/release/eugenpt/ep_pydicom_anonymizer)](https://github.com/eugenpt/ep_pydicom_anonymizer/releases)

A fast, parallel DICOM anonymizer tool with GUI and CLI support. Removes PHI (Patient Health Information) like names, IDs, dates, and UIDs while preserving file structure.

## Features
- **Deterministic UID replacement** for consistent anonymization across files.
- **Parallel processing** via `ProcessPoolExecutor`.
- **Configurable fields** via `config.txt` (e.g., clear PatientName, StudyDate).
- **Hybrid mode**: GUI for interactive use; CLI for scripting.
- **Cross-platform** (Windows focus; Linux/macOS via Python).

## Quick Start

### Prerequisites
- Python 3.8+
- Install deps: `pip install -r requirements.txt`

### CLI Usage
```bash
python batch.py /path/to/input /path/to/output -c config.txt
```

### GUI Usage
```bash
python batch.py
```
- Select folders via dialogs.
- Edit `config.txt` for custom fields.

### Build Executable (Windows)
```bash
.\make_exe.bat
```
-> Creates `dist/DICOM_Anonymizer.exe` (hybrid CLI/GUI).

## Configuration
Edit `config.txt` to customize (INI format):
```
[Fields]
PatientName = ""
PatientID = ""
StudyDate = ""
# Hex tags supported: 0010,0010 = "Anon"
```

## Releases
- Download from [Releases](https://github.com/yourusername/ep_pydicom_anonymizer/releases).
- ZIP includes: `.exe`, `config.txt`, `README.txt`.

## Development
- Build: See `make_exe.bat`.
- Release: `git tag -a v1.0.0 -m "Release"` + `git push origin v1.0.0` → Auto-builds ZIP.

## License
MIT – See [LICENSE](LICENSE).

## Contributing
Fork, PR, or issues welcome! Contact: eugen.pt@gmail.com.
