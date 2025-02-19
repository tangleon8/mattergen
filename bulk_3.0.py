import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.ext.matproj import MPRester
import os
import pandas as pd

# 🔑 Replace with your Materials Project API Key
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"

# Initialize the Materials Project API
mpr = MPRester("H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T")

# Initialize StructureMatcher
matcher = StructureMatcher()

# 🔍 Your local path to CIF files
cif_folder = r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\2.0"

# ✅ Check if folder exists
if not os.path.exists(cif_folder):
    print(f"\n❌ Error: The folder path '{cif_folder}' does not exist.")
    exit()

# 📂 List all CIF files
cif_files = [f for f in sorted(os.listdir(cif_folder)) if f.endswith(".cif")]

if not cif_files:
    print("\n❌ Error: No CIF files found in the specified folder.")
    exit()

print(f"\n📂 Found {len(cif_files)} CIF files. Processing all...")

# 📊 Data storage
results = []

# 📖 Read and process CIF files
for cif_file in cif_files:
    file_path = os.path.join(cif_folder, cif_file)

    try:
        # Load structure
        structure = Structure.from_file(file_path)

        # 🔄 Convert atomic positions to ensure correct dtype
        structure.frac_coords = np.array(structure.frac_coords, dtype=np.float64)

        formula = structure.composition.alphabetical_formula  # Standardized formula

        print(f"\n📖 Processing {cif_file} | Formula: {formula}")

        # 🔍 Query MP database for similar compositions
        existing_materials = mpr.get_structures(formula)

        match_found = False

        if existing_materials:
            print(f"🔬 {len(existing_materials)} similar materials found in Materials Project.")

            for mp_struct in existing_materials:
                # Convert atomic positions to the correct dtype for MP structure
                mp_struct.frac_coords = np.array(mp_struct.frac_coords, dtype=np.float64)

                if matcher.fit(structure, mp_struct):
                    match_found = True
                    print(f"✅ Structure {cif_file} MATCHES existing MP structure.")
                    break  # No need to check further

        # 🏷 Mark as "Existing" or "Novel"
        status = "Existing" if match_found else "Novel"
        results.append({"CIF File": cif_file, "Formula": formula, "Status": status})

    except Exception as e:
        print(f"❌ Error processing {cif_file}: {e}")

# 📊 Save results to CSV
df = pd.DataFrame(results)
csv_path = os.path.join(cif_folder, "generated_structures_analysis.csv")
df.to_csv(csv_path, index=False)

print(f"\n📁 Analysis complete! Results saved to: {csv_path}")
