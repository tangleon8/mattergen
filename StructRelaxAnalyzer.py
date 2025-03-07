import os
from pymatgen.core import Structure, Lattice
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
from matgl.ext.ase import Relaxer
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# API Key for Materials Project
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# Setup structure matcher
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

# Define potential (replace 'pot' with actual potential)
pot = None  # Define appropriate potential
relaxer = Relaxer(potential=pot)

# Define CIF folders
cif_folders = [
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\7.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\5.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\6.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\3.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\2.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\4.0"
]

# Validate folders and collect CIF files
cif_files = []
for folder in cif_folders:
    if os.path.exists(folder):
        cif_files.extend([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".cif")])
    else:
        print(f"❌ Error: The folder path '{folder}' does not exist.")

if not cif_files:
    print("❌ Error: No CIF files found.")
    exit()

print(f"📂 Found {len(cif_files)} CIF files. Processing...")


# Function to read and process CIF files
def read_cif_file(cif_file):
    try:
        structure = Structure.from_file(cif_file)
        formula = structure.composition.alphabetical_formula
        return os.path.basename(cif_file), structure, formula
    except Exception as e:
        return os.path.basename(cif_file), None, None


# Process CIF files in parallel
pymatgen_structures = {}
formulas_to_files = defaultdict(list)

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = {executor.submit(read_cif_file, cif): cif for cif in cif_files}
    for future in as_completed(futures):
        name, structure, formula = future.result()
        if structure and formula:
            pymatgen_structures[name] = structure
            formulas_to_files[formula].append(name)

# Query Materials Project for matching structures
mp_structures = {formula: mpr.get_structures(formula) for formula in formulas_to_files.keys()}

# Structure Matching & Novelty Analysis
is_novel = {}
matched_structures = {}

for cif_file, local_structure in pymatgen_structures.items():
    formula = local_structure.composition.alphabetical_formula
    existing_materials = mp_structures.get(formula)

    if existing_materials:
        match_found = any(matcher.fit(local_structure, mp) for mp in existing_materials)
        is_novel[cif_file] = not match_found
        if match_found:
            matched_structures[cif_file] = formula
    else:
        is_novel[cif_file] = True

# Relax structures and compute energy differences
energy_differences = {}
relaxed_structures = {}

for cif_file, structure in pymatgen_structures.items():
    try:
        relax_results = relaxer.relax(structure, fmax=0.01)
        final_structure = relax_results["final_structure"]
        final_energy = relax_results["trajectory"].energies[-1]
        relaxed_structures[cif_file] = final_structure
        energy_differences[cif_file] = (final_energy - structure.energy_per_atom) * 1000  # Convert to meV/atom
    except Exception as e:
        print(f"❌ Error relaxing {cif_file}: {e}")

# Report results
novel_count = sum(1 for v in is_novel.values() if v)
total_checked = len(is_novel)
matching_count = len(matched_structures)

print("\n=== Summary ===")
print(f"Novel structures: {novel_count}/{total_checked} (Ratio: {novel_count / total_checked:.2%})")
print(f"Matched structures: {matching_count}")
print(f"Energy differences > 20 meV/atom: {sum(1 for v in energy_differences.values() if v > 20)}")

# Print novel CIF files
if novel_count:
    print("Novel CIF files:", ", ".join([cif for cif, novel in is_novel.items() if novel]))
