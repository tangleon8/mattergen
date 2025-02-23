from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
import os
from collections import defaultdict

# API key and MPRester setup
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"  # Ensure this is your valid key
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# StructureMatcher configuration
matcher = StructureMatcher(
    ltol=0.2,           # Lattice tolerance
    stol=0.3,           # Site tolerance
    angle_tol=5.0,      # Angle tolerance in degrees
    primitive_cell=True,
    scale=True,
    comparator=OrderDisorderElementComparator(),
    attempt_supercell=True,
    allow_subset=True
)

# CIF folder path
cif_folder = r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\2.0"

# Verify folder exists
if not os.path.exists(cif_folder):
    print(f"Error: Folder '{cif_folder}' does not exist.")
    exit()

# Get all CIF files
cif_files = [f for f in sorted(os.listdir(cif_folder)) if f.endswith(".cif")]
if not cif_files:
    print("Error: No CIF files found.")
    exit()

print(f"Found {len(cif_files)} CIF files. Processing all...")

# Load structures
pymatgen_structures = {}
formulas_to_files = defaultdict(list)  # Map formulas to CIF files for batching
for cif_file in cif_files:
    try:
        file_path = os.path.join(cif_folder, cif_file)
        structure = Structure.from_file(file_path)
        formula = structure.composition.alphabetical_formula
        pymatgen_structures[cif_file] = structure
        formulas_to_files[formula].append(cif_file)
        print(f"Loaded {cif_file} | Formula: {formula}")
    except Exception as e:
        print(f"Error loading {cif_file}: {e}")

# Optional: Placeholder for Ovito integration (e.g., visualization)
# TODO: If needed, use Ovito Python API to load and inspect structures here

# Batch query Materials Project for unique formulas
mp_structures = {}  # Cache MP structures by formula
for formula in formulas_to_files.keys():
    try:
        print(f"Querying Materials Project for {formula}...")
        mp_structures[formula] = mpr.get_structures(formula)
    except Exception as e:
        print(f"Error querying {formula}: {e}")
        mp_structures[formula] = None

# Track novelty
is_novel = {}
error_files = []
for cif_file, local_structure in pymatgen_structures.items():
    formula = local_structure.composition.alphabetical_formula
    try:
        existing_materials = mp_structures.get(formula)
        if existing_materials is None:
            # Query failed, mark as unchecked
            is_novel[cif_file] = None
            error_files.append((cif_file, "MP query failed"))
        elif existing_materials:
            # Check for structural match
            match_found = any(matcher.fit(local_structure, mp_structure)
                            for mp_structure in existing_materials)
            is_novel[cif_file] = not match_found
            print(f"{cif_file}: {'novel' if not match_found else 'exists in MP'}")
        else:
            # No structures with this formula in MP
            is_novel[cif_file] = True
            print(f"{cif_file}: novel (no formula match in MP)")
    except Exception as e:
        print(f"Error checking {cif_file}: {e}")
        is_novel[cif_file] = None
        error_files.append((cif_file, str(e)))

# Detailed output
print("\n=== Structure Status ===")
novel_structures = []
for cif_file in sorted(is_novel.keys()):
    status = is_novel[cif_file]
    if status is True:
        novel_structures.append(cif_file)
        print(f"{cif_file}: novel")
    elif status is False:
        print(f"{cif_file}: exists in MP")
    else:
        print(f"{cif_file}: could not be checked")

# Calculate ratio
novel_count = sum(1 for status in is_novel.values() if status is True)
total_checked = sum(1 for status in is_novel.values() if status is not None)
if total_checked > 0:
    ratio = novel_count / total_checked
    print(f"\n=== Summary ===")
    print(f"Novel structures: {novel_count}/{total_checked} (Ratio: {ratio:.2%})")
    print(f"Failed checks: {len(error_files)}")
    if novel_structures:
        print("Novel CIF files:", ", ".join(novel_structures))
    if error_files:
        print("Errors encountered:")
        for file, error in error_files:
            print(f"  {file}: {error}")
else:
    print("\nNo structures were successfully checked.")