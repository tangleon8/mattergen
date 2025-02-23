from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Replace with your NEW Materials Project API key
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"  # Keep this private!

# Initialize the Materials Project API
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# Initialize StructureMatcher with valid parameters
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

# List of folders to process
cif_folders = [
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\7.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\5.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\6.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\3.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\2.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\4.0"
]

# Check if folders exist
for folder in cif_folders:
    if not os.path.exists(folder):
        print(f"\n❌ Error: The folder path '{folder}' does not exist.")
        exit()

# Collect all CIF files from the folders
cif_files = []
for folder in cif_folders:
    cif_files.extend([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".cif")])

if not cif_files:
    print("\n❌ Error: No CIF files found in the specified folders.")
    exit()

print(f"\n📂 Found {len(cif_files)} CIF files across all folders. Processing the first 128...")

# Function to read a single CIF file
def read_cif_file(cif_file):
    try:
        structure = Structure.from_file(cif_file)
        formula = structure.composition.alphabetical_formula  # Standardized formula
        print(f"✅ Successfully loaded {os.path.basename(cif_file)} | Extracted Formula: {formula}")
        return os.path.basename(cif_file), structure, formula
    except Exception as e:
        print(f"❌ Error loading {os.path.basename(cif_file)}: {e}")
        return os.path.basename(cif_file), None, None

# Read and process CIF files in parallel
pymatgen_structures = {}
extracted_formulas = []

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    future_to_cif = {executor.submit(read_cif_file, cif_file): cif_file for cif_file in cif_files[:128]}

    for future in as_completed(future_to_cif):
        cif_file = future_to_cif[future]
        try:
            cif_file, structure, formula = future.result()
            if structure and formula:
                pymatgen_structures[cif_file] = structure
                extracted_formulas.append(formula)
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(cif_file)}: {e}")

# Print extracted formulas before querying Materials Project
print("\n🔍 Extracted formulas for lookup:", extracted_formulas)

# Query Materials Project database for each formula INDIVIDUALLY
if extracted_formulas:
    matched_results = {}

    for cif_file, local_structure in pymatgen_structures.items():
        formula = local_structure.composition.alphabetical_formula
        try:
            print(f"\n🔎 Searching for: {formula} in Materials Project...")
            existing_materials = mpr.get_structures(formula)

            if existing_materials:
                # Compare local structure with each structure from Materials Project
                match_found = False
                for mp_structure in existing_materials:
                    if matcher.fit(local_structure, mp_structure):  # Use StructureMatcher
                        print(f"✅ Match found for {formula} in {cif_file}")
                        matched_results[cif_file] = mp_structure.composition.formula
                        match_found = True
                        break

                if not match_found:
                    print(f"❌ No structural match found for {formula} in {cif_file}")
            else:
                print(f"❌ No match found for {formula}")

        except Exception as e:
            print(f"\n❌ Error querying {formula}: {e}")

# Print final results
if matched_results:
    print("\n✅ Matching structures found in Materials Project:")
    for cif_file, matched_formula in matched_results.items():
        print(f"{cif_file} → {matched_formula}")
else:
    print("\n❌ No matches found in Materials Project.")