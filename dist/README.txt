=================================================================
       EP PyDICOM Anonymizer v1.0 — DICOM Anonymizer
=================================================================

--------------------------------------------------------------------
 OVERVIEW
--------------------------------------------------------------------
Anonymizes **thousands of DICOM files in seconds** while preserving:
• Folder structure
• Study/Series relationships

Features:
• Parallel processing (8+ cores)
• GUI with progress bar + timer
• Clean filenames: anon_000001.dcm
• Configurable via config.txt
• Removes all PHI (name, ID, dates, institution)
• CLI for automation
• Runs on Windows 7–11

--------------------------------------------------------------------
 PACKAGE CONTENTS
--------------------------------------------------------------------
DICOM_Anonymizer_v1.0.0.exe   ← Double-click to run
config.txt                    ← Full anonymization (all fields cleared)
README.txt                    ← This file

--------------------------------------------------------------------
 USAGE (GUI)
--------------------------------------------------------------------
1. Double-click DICOM_Anonymizer_v1.0.0.exe
2. Select:
   • Input folder (source DICOMs)
   • Output folder (anonymized results)
   • (Optional) config.txt
3. Click “Start Anonymization”
4. Watch progress
5. Done — files are anonymized

--------------------------------------------------------------------
 USAGE (CLI)
--------------------------------------------------------------------
Open CMD or PowerShell:

1. Basic:
   DICOM_Anonymizer_v1.0.0.exe "C:\DICOM\In" "C:\DICOM\Out"

2. With config:
   DICOM_Anonymizer_v1.0.0.exe "C:\In" "C:\Out" -c "config.txt"

3. Custom fields:
   DICOM_Anonymizer_v1.0.0.exe "C:\In" "C:\Out" PatientName="Anonymous" PatientSex="M"

4. Hex tags:
   DICOM_Anonymizer_v1.0.0.exe "C:\In" "C:\Out" "0010,0010"="Patient" "0008,0050"=""

--------------------------------------------------------------------
 CONFIG.TXT — EXAMPLE
--------------------------------------------------------------------
[Fields]
; Clear fields
PatientName      = ""
PatientID        = ""
PatientBirthDate = ""
StudyDate        = ""

; Replace values
InstitutionName  = "Clinic XYZ"
ReferringPhysicianName = "Dr^Anonymous"

; Hex format
0010,0010 = "Patient"
0008,1030 = ""

--------------------------------------------------------------------
 SUPPORT
--------------------------------------------------------------------
GitHub: https://github.com/eugenpt/ep_pydicom_anonymizer

--------------------------------------------------------------------
 LICENSE
--------------------------------------------------------------------
MIT License — Free for personal and commercial use.
Modification and redistribution allowed with license retention.

© 2025 EP | MIT License

=================================================================