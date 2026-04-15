# Agentic Executor — Real Workflow Example

This folder contains a small broken Python project (`phi_calculator/`) that computes
the Golden Ratio (φ ≈ 1.6180339887...).

The project has four bugs spread across four files:
- wrong module name in an import (`computer` instead of `calculator`)
- wrong formula (`sqrt(4)` instead of `sqrt(5)`, extra `* 1.1`, floor instead of round)
- imports from a non-existent module (`phi_calculator.compute`)
- wrong validation bounds and wrong type check

The walkthrough below shows how an agent using Agentic Executor fixes all of them
in **three calls** instead of many individual tool operations.

---

## The bugs (before fix)

| File | Lines | Bug |
|------|-------|-----|
| `main.py` | 4 | `from phi_calculator.computer import` — module should be `calculator` |
| `calculator.py` | 9–16 | `sqrt(4)` instead of `sqrt(5)`, extra `* 1.1`, floor instead of round |
| `formatter.py` | 4–7 | imports from `phi_calculator.compute` — module does not exist |
| `validator.py` | 7–15 | wrong type check (`== float`), wrong bounds (`< 0`, `> 100`) |

---

## Call 1 — Scan and understand the codebase

```bash
python -m agentic_executor.cli --thought-stdin <<'EOF'
CACHE = 'example/phi_calculator/.agentic_executor/metadata.json'
execute('scan_codebase', {'path': 'example/phi_calculator', 'cache': CACHE})
meta = execute('get_metadata', {'type': 'structure', 'cache': CACHE})

for path, data in meta['data']['files'].items():
    print(f"\n--- {path} ---")
    print(f"  lines     : {data.get('lines', '?')}")
    print(f"  functions : {[f['name'] + ':' + str(f['line']) for f in data.get('functions', [])]}")
    print(f"  imports   : {data.get('imports', [])}")
EOF
```

**Output:**

```
--- calculator.py ---
  lines     : 53
  functions : ['compute_phi:9', 'phi_power:19', 'phi_ratio_check:25', 'fibonacci_approx:32', 'convergence_table:42']
  imports   : ['math']

--- formatter.py ---
  lines     : 48
  functions : ['format_result:13', 'format_powers:20', 'format_convergence:30', 'full_report:40']
  imports   : ['os', 'phi_calculator.compute', 'phi_calculator.compute']

--- main.py ---
  lines     : 21
  functions : ['run:9']
  imports   : ['phi_calculator.computer', 'phi_calculator.formatter', 'phi_calculator.validator']

--- validator.py ---
  lines     : 53
  functions : ['is_valid_precision:7', 'is_valid_power:18', 'is_positive_float:25', 'validate_ratio_inputs:32', 'validate_fibonacci_n:44']
  imports   : []
```

**What this reveals:**
- `main.py` imports from `phi_calculator.computer` — a module that does not exist
- `formatter.py` imports twice from `phi_calculator.compute` — also non-existent
- `compute_phi` starts at line 9 in `calculator.py` — need to read the body
- `is_valid_precision` starts at line 7 in `validator.py` — need to read the body

---

## Call 2 — Read all files in one shot

```bash
python -m agentic_executor.cli --thought-stdin <<'EOF'
files = [
    'example/phi_calculator/main.py',
    'example/phi_calculator/calculator.py',
    'example/phi_calculator/formatter.py',
    'example/phi_calculator/validator.py',
]

for f in files:
    r = execute('read', {'path': f})
    if r['success']:
        print(f"\n{'='*60}")
        print(f"FILE: {f}")
        print('='*60)
        for i, line in enumerate(r['data']['content'].split('\n'), 1):
            print(f"{i:3}  {line}")
EOF
```

**Output (relevant excerpts):**

```
============================================================
FILE: example/phi_calculator/main.py
============================================================
  4  from phi_calculator.computer import compute_phi       # BUG: wrong module name

============================================================
FILE: example/phi_calculator/calculator.py
============================================================
  8  # BUG: lines 9-14 — wrong formula and wrong constant, needs full replacement
  9  def compute_phi(precision: int) -> float:
 10      # incorrect: uses wrong base constant
 11      phi = (1 + math.sqrt(4)) / 2
 12      # incorrect: applies an extra meaningless operation
 13      phi = phi * 1.1
 14      # incorrect: truncates instead of rounding
 15      factor = 10 ** (precision - 2)
 16      return math.floor(phi * factor) / factor

============================================================
FILE: example/phi_calculator/formatter.py
============================================================
  4  # BUG: lines 4-8 — imports a non-existent module and unused symbol
  5  import os
  6  from phi_calculator.compute import phi_power        # BUG: wrong module
  7  from phi_calculator.compute import convergence_table  # BUG: same wrong module

============================================================
FILE: example/phi_calculator/validator.py
============================================================
  6  # BUG: lines 7-13 — wrong bounds and wrong return type, needs full replacement
  7  def is_valid_precision(precision) -> bool:
  8      # should accept int only, range 1–50
  9      if type(precision) == float:    # wrong: should check for int
 10          return False
 11      if precision < 0:               # wrong: should be < 1
 12          return False
 13      if precision > 100:             # wrong: should be > 50
 14          return False
 15      return True                     # missing: should also return False for non-int types
```

**What this reveals:**
- `calculator.py` lines 9–16: full function body is wrong, needs complete replacement
- `formatter.py` lines 4–7: four import lines to fix
- `validator.py` lines 7–15: entire function body to replace
- All exact line numbers confirmed

---

## Call 3 — Fix everything in one batch

```bash
python -m agentic_executor.cli --thought-stdin <<'EOF'
edits = [
    # main.py line 4 — wrong module name
    {'path': 'example/phi_calculator/main.py',       'line': 4,  'new': 'from phi_calculator.calculator import compute_phi'},

    # calculator.py lines 9-16 — wrong formula, replace entire function body
    {'path': 'example/phi_calculator/calculator.py', 'line': 9,  'new': 'def compute_phi(precision: int) -> float:'},
    {'path': 'example/phi_calculator/calculator.py', 'line': 10, 'new': '    """Return phi = (1 + sqrt(5)) / 2 rounded to precision decimal places."""'},
    {'path': 'example/phi_calculator/calculator.py', 'line': 11, 'new': '    phi = (1 + math.sqrt(5)) / 2'},
    {'path': 'example/phi_calculator/calculator.py', 'line': 12, 'new': '    return round(phi, precision)'},
    {'path': 'example/phi_calculator/calculator.py', 'line': 13, 'new': ''},
    {'path': 'example/phi_calculator/calculator.py', 'line': 14, 'new': ''},
    {'path': 'example/phi_calculator/calculator.py', 'line': 15, 'new': ''},
    {'path': 'example/phi_calculator/calculator.py', 'line': 16, 'new': ''},

    # formatter.py lines 4-7 — remove bad imports, add correct ones
    {'path': 'example/phi_calculator/formatter.py',  'line': 4,  'new': ''},
    {'path': 'example/phi_calculator/formatter.py',  'line': 5,  'new': ''},
    {'path': 'example/phi_calculator/formatter.py',  'line': 6,  'new': 'from phi_calculator.calculator import phi_power'},
    {'path': 'example/phi_calculator/formatter.py',  'line': 7,  'new': 'from phi_calculator.calculator import convergence_table'},

    # validator.py lines 7-15 — replace entire is_valid_precision body
    {'path': 'example/phi_calculator/validator.py',  'line': 7,  'new': 'def is_valid_precision(precision) -> bool:'},
    {'path': 'example/phi_calculator/validator.py',  'line': 8,  'new': '    """Accept only int in range 1–50."""'},
    {'path': 'example/phi_calculator/validator.py',  'line': 9,  'new': '    if not isinstance(precision, int):'},
    {'path': 'example/phi_calculator/validator.py',  'line': 10, 'new': '        return False'},
    {'path': 'example/phi_calculator/validator.py',  'line': 11, 'new': '    return 1 <= precision <= 50'},
    {'path': 'example/phi_calculator/validator.py',  'line': 12, 'new': ''},
    {'path': 'example/phi_calculator/validator.py',  'line': 13, 'new': ''},
    {'path': 'example/phi_calculator/validator.py',  'line': 14, 'new': ''},
    {'path': 'example/phi_calculator/validator.py',  'line': 15, 'new': ''},
]

ok = 0
fail = 0
for e in edits:
    r = execute('replace', {'path': e['path'], 'line': e['line'], 'new': e['new']})
    if r['success']:
        ok += 1
    else:
        fail += 1
        print(f"FAIL  {e['path']}:{e['line']}  →  {r['error']}")

print(f"\nDone: {ok} edits applied, {fail} failed")
EOF
```

**Output:**

```
Done: 22 edits applied, 0 failed
```

---

## Verify

```bash
cd example && python -m phi_calculator.main
```

**Output:**

```
========================================
  Golden Ratio
  phi (precision=12): 1.618033988750
========================================
```

---

## Why three calls instead of many

| Approach | Tool calls |
|----------|-----------|
| Native tools (Read each file separately, Edit each bug) | ~10–15 calls |
| Agentic Executor | **3 calls** |

The agent scanned once, read everything in one loop, then applied 22 targeted
line-level edits across four files in a single thought. No round-trips, no
context switches between files, no lost state.
