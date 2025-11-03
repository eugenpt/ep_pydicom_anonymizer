# anonymizer.py
from __future__ import annotations

import hashlib
import traceback
from pathlib import Path
from typing import Dict, Tuple

import pydicom
from pydicom.tag import Tag
from pydicom.uid import UID, generate_uid


# --------------------------------------------------------------------------- #
# Per-process deterministic UID cache
# --------------------------------------------------------------------------- #
STUDY_PREFIX  = "1.2.826.0.1.3680043.8.498.1"
SERIES_PREFIX = "1.2.826.0.1.3680043.8.498.2"

# This dict is recreated in every child process → safe, no locks
_uid_cache: Dict[str, UID] = {}


def _det_uid(orig: str, prefix: str) -> UID:
    """Deterministic UID. Cached per process."""
    if not orig:
        return generate_uid()
    if orig not in _uid_cache:
        h = hashlib.sha256(orig.encode()).hexdigest()[:32]
        parts = [str(int(h[i:i + 8], 16)) for i in range(0, 32, 8)]
        uid_str = ".".join([prefix] + parts)[:64].ljust(64, "0")
        _uid_cache[orig] = UID(uid_str)
    return _uid_cache[orig]


# --------------------------------------------------------------------------- #
# Core: Anonymize one file
# --------------------------------------------------------------------------- #
def set_field_safely(ds: pydicom.Dataset, tag: Tag, value: str) -> None:
    try:
        if tag in ds:
            ds[tag].value = value
        else:
            vr = getattr(ds, "tag_to_vr", lambda t: "LO")(tag)
            ds.add_new(tag, vr, value)
    except Exception:
        pass


def anonymize_one(
    args: Tuple[Path, Path, Path, Dict[Tag, str], int]
) -> Tuple[str, str] | None:
    fpath, in_root, out_root, fields, idx = args

    try:
        ds = pydicom.dcmread(fpath, force=True)

        # 1. Fields
        for tag, val in fields.items():
            set_field_safely(ds, tag, val)

        # 2. UIDs
        o_study  = str(ds.get("StudyInstanceUID", ""))
        o_series = str(ds.get("SeriesInstanceUID", ""))

        ds.StudyInstanceUID  = _det_uid(o_study,  STUDY_PREFIX)
        ds.SeriesInstanceUID = _det_uid(o_series, SERIES_PREFIX)
        ds.SOPInstanceUID    = generate_uid()

        # 3. References
        if "ReferencedSOPInstanceUID" in ds:
            ds.ReferencedSOPInstanceUID = ds.SOPInstanceUID
        if "ReferencedSeriesSequence" in ds:
            for itm in ds.ReferencedSeriesSequence:
                orig = itm.get("SeriesInstanceUID", "")
                if orig:
                    itm.SeriesInstanceUID = _det_uid(orig, SERIES_PREFIX)
        if "ReferencedStudySequence" in ds:
            for itm in ds.ReferencedStudySequence:
                orig = itm.get("StudyInstanceUID", "")
                if orig:
                    itm.StudyInstanceUID = _det_uid(orig, STUDY_PREFIX)

        # 4. Private tags
        for tag in list(ds.keys()):
            if tag.is_private:
                del ds[tag]

        # 5. Write
        rel_dir = fpath.relative_to(in_root).parent
        out_dir = out_root / rel_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"anon_{idx:06d}.dcm"
        pydicom.dcmwrite(out_file, ds, write_like_original=False)

        return None

    except Exception:
        return (str(fpath), traceback.format_exc())