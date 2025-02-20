from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.ext.matproj import MPRester
import os

# API Key for Materials Project
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# Initialize StructureMatcher
matcher = StructureMatcher()

# Local CIF folder path
cif_folder = r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\7.0"

# Check if folder exists
if not os.path.exists(cif_folder):
    print(f"\n❌ Error: The folder path '{cif_folder}' does not exist.")
    exit()

# List all CIF files
cif_files = [f for f in sorted(os.listdir(cif_folder)) if f.endswith(".cif")]

if not cif_files:
    print("\n❌ Error: No CIF files found in the specified folder.")
    exit()

print(f"\n📂 Found {len(cif_files)} CIF files. Processing the first 3...")

# Read and process CIF files
pymatgen_structures = {}  # Dictionary to store loaded structures
extracted_formulas = []  # List to store extracted chemical formulas

for cif_file in cif_files[:128]:  # Process first 3 files
    file_path = os.path.join(cif_folder, cif_file)
    print(f"📖 Reading {cif_file}...")

    try:
        # Load the structure from the CIF file
        structure = Structure.from_file(file_path)

        # Extract the standardized chemical formula (alphabetical order)
        formula = structure.composition.alphabetical_formula

        # Store the structure and formula for later use
        pymatgen_structures[cif_file] = structure
        extracted_formulas.append(formula)
        print(f"✅ Successfully loaded {cif_file} | Extracted Formula: {formula}")
    except Exception as e:
        print(f"❌ Error loading {cif_file}: {e}")

# Print extracted formulas before querying Materials Project
print("\n🔍 Extracted formulas for lookup:", extracted_formulas)

# Query Materials Project database for each formula individually
matched_results = {}  # Dictionary to store matching results

if extracted_formulas:
    for formula in extracted_formulas:
        try:
            print(f"\n🔎 Searching for: {formula} in Materials Project...")
            # Query Materials Project for structures matching the formula
            existing_materials = mpr.get_structures(formula)

            if existing_materials:
                # If a match is found, store the first matching structure's formula
                print(f"✅ Match found for {formula}")
                matched_results[formula] = existing_materials[0].composition.formula
            else:
                print(f"❌ No match found for {formula}")

        except Exception as e:
            print(f"\n❌ Error querying {formula}: {e}")

# Print final results
if matched_results:
    print("\n✅ Matching structures found in Materials Project:")
    for formula, matched_formula in matched_results.items():
        print(f"{formula} → {matched_formula}")
else:
    print("\n❌ No matches found in Materials Project.")
