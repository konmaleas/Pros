# Cleanup Report — Pros Project

## 1. Delete Entirely — No Value, Pure Weight

| Path | Size | Reason |
|------|------|--------|
| `archive/` | 86 MB | 20 versioned copies of the same pipeline; git history already serves this purpose |
| `claude/` | 13 MB | Working scratch area — old outputs, one experimental file (`redesigned/fully.py`), chat summaries |
| `files/` | 15 MB | Historical batch report outputs |
| `output/` | 24 MB | Processing artifacts from old runs (already gitignored) |
| `notes/debug_sessions/` | — | 30+ raw debug text dumps |
| `pros_directory_tree.txt` | 28 KB | Stale snapshot, `tree` can regenerate it |
| `migrate_structure.py` | — | One-shot migration script, already ran |
| `test.py` | — | Empty file at root |
| `files.tar.gz`, `v18.tar.gz` | 1.1 MB | Redundant compressed archives at root |

---

## 2. Consolidate — Duplicates in `modules/`

`modules/` is a legacy utility library being superseded by `src/pdf_pipeline/utils/`. Several files are **exact duplicates**:

- `modules/letter_conversion.py` = `src/pdf_pipeline/utils/letter_conversion.py` (263 lines each)
- `modules/dates.py` = `src/pdf_pipeline/utils/dates.py` (150 lines each)
- `list_oper.py` + `list_opers.py` + `list_opers_com.py` — three overlapping versions; only the combined one matters

**Decision needed:** Is `modules/` still imported anywhere in `src/`? If not, delete the whole folder. If yes, migrate the unique parts into `src/pdf_pipeline/utils/` and delete `modules/`.

---

## 3. Fix `.gitignore` — Things Currently Untracked but Not Explicitly Ignored

```
files/
claude/
notes/debug_sessions/
pros_directory_tree.txt
files.tar.gz
v18.tar.gz
*.zip
start_time.txt
```

---

## 4. Keep As-Is

| Path | Reason |
|------|--------|
| `src/pdf_pipeline/` | Clean, well-structured production code |
| `config/` | Small, clean configuration |
| `tests/fixtures/` | 44 test files — useful |
| `docs/` | Documentation |
| `notes/chat_summaries/` | 19 files of development context — borderline, your call |
| `requirements.txt`, `README.md`, `MIGRATION_GUIDE.txt` | Keep |

---

## 5. Duplicate Modules Detail

### Email Reader (modules/)
- `email_reader.py` (162 lines) vs `email_reader_.py` (177 lines) — different implementations, likely one is older

### List Operations (3-way duplication in modules/)
- `list_oper.py` (379 lines)
- `list_opers.py` (316 lines)
- `list_opers_com.py` (444 lines) — appears to be the comprehensive version; the other two can be deleted

### Core Pipeline (extensive duplication across archive/)
Same 4–5 core files repeated in every versioned directory:
- `text_extractor.py` — 17+ copies
- `text_processor.py` — 17+ copies
- `adaptive_filter.py` — 17+ copies
- `pattern_analyzer.py` — 17+ copies
- `batch_processor.py` — 4+ copies

Production versions live in `src/pdf_pipeline/core/` — all archive copies are obsolete.

---

## 6. Expected Size After Cleanup

| | Size |
|-|------|
| Before | ~140 MB |
| After | ~2 MB |

---

## 7. Suggested Order of Operations

1. Verify `modules/` is not imported by `src/` — then decide its fate
2. Delete dead-weight directories: `archive/`, `claude/`, `files/`, `output/`
3. Update `.gitignore`
4. Clean root junk files (`test.py`, `pros_directory_tree.txt`, `migrate_structure.py`, compressed archives)
5. Commit the result
