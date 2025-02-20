from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
import os

# API key and MPRester setup
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# StructureMatcher configuration
matcher = StructureMatcher(
    ltol=0.2,
    stol=0.3,
    angle_tol=5.0,
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
for cif_file in cif_files:
    try:
        structure = Structure.from_file(os.path.join(cif_folder, cif_file))
        pymatgen_structures[cif_file] = structure
    except Exception as e:
        print(f"Error loading {cif_file}: {e}")

# Track novelty
is_novel = {}
for cif_file, local_structure in pymatgen_structures.items():
    formula = local_structure.composition.alphabetical_formula
    try:
        existing_materials = mpr.get_structures(formula)
        if existing_materials:
            # Check for structural match
            match_found = any(matcher.fit(local_structure, mp_structure) for mp_structure in existing_materials)
            is_novel[cif_file] = not match_found
        else:
            # No structures with this formula in MP
            is_novel[cif_file] = True
    except Exception as e:
        print(f"Error querying {formula}: {e}")
        is_novel[cif_file] = None

# Print status for each structure
print("\nStructure Status:")
for cif_file in sorted(is_novel.keys()):
    status = is_novel[cif_file]
    if status is True:
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
    print(f"\nOverall ratio of novel structures: {ratio:.2%} ({novel_count}/{total_checked})")
else:
    print("\nNo structures were successfully checked.")