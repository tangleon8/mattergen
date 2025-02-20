
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
import os

MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"

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

# local
cif_folder = r"C:\Users\Leon\OneDrive\Documents\generated_crystals_cif_4.0\tmp"

# Check if folder exists
if not os.path.exists(cif_folder):
    print(f"\n❌ Error: The folder path '{cif_folder}' does not exist.")
    exit()

# List all CIF files
cif_files = [f for f in sorted(os.listdir(cif_folder)) if f.endswith(".cif")]

if not cif_files:
    print("\n❌ Error: No CIF files found in the specified folder.")
    exit()

print(f"\n📂 Found {len(cif_files)} CIF files. Processing the first 128...")

# Read and process CIF files
pymatgen_structures = {}
extracted_formulas = []

for cif_file in cif_files[:128]:  # Process first 128 files
    file_path = os.path.join(cif_folder, cif_file)
    print(f"📖 Reading {cif_file}...")

    try:
        structure = Structure.from_file(file_path)
        formula = structure.composition.alphabetical_formula  # Standardized formula
        pymatgen_structures[cif_file] = structure
        extracted_formulas.append(formula)
        print(f"✅ Successfully loaded {cif_file} | Extracted Formula: {formula}")
    except Exception as e:
        print(f"❌ Error loading {cif_file}: {e}")

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