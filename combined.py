from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict


MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"
mpr = MPRester(MATERIALS_PROJECT_API_KEY)

# StructureMatcher configuration
matcher = StructureMatcher(
    ltol=0.2, # lattice parameter tolerance
    stol=0.3, #site tolerance for atomic position
    angle_tol=5.0, # Tolerance for angles between unit cell vectors
    primitive_cell=True, #Reduce the strcutures to primitive cells before comparison
    scale=True, # Same scale
    comparator=OrderDisorderElementComparator(), # Ordered vs Disordered
    attempt_supercell=True, #Matching of supercell structures
    allow_subset=True #Subset comaprison
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

for folder in cif_folders:
    if not os.path.exists(folder):
        print(f"\n❌ Error: The folder path '{folder}' does not exist.")
        exit()

# Collect all CIF files from the folders
cif_files = []
for folder in cif_folders:
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".cif")]
    cif_files.extend(files)

if not cif_files:
    print("\n❌ Error: No CIF files found in the specified folders.")
    exit()

print(f"\n📂 Found {len(cif_files)} CIF files across all folders. Processing all...")

# Function to read a single CIF file
def read_cif_file(cif_file):
    try:
        structure = Structure.from_file(cif_file) #Load the structure from CIF file
        formula = structure.composition.alphabetical_formula #Get the chemcial formula in alphabetical order
        print(f"✅ Loaded {os.path.basename(cif_file)} | Formula: {formula}")
        return os.path.basename(cif_file), structure, formula #Returns file name, structure, and formula
    except Exception as e:
        print(f"❌ Error loading {os.path.basename(cif_file)}: {e}")
        return os.path.basename(cif_file), None, None #if values failed return none

# Read CIF files in parallel for faster compute
pymatgen_structures = {} #Dictionary to store sucessful structures
formulas_to_files = defaultdict(list) # Group CIF files by their chemical formulas
with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor: # Use all available CPU cores for parallel processing
    # Submit each CIF file to be processed
    future_to_cif = {executor.submit(read_cif_file, cif_file): cif_file for cif_file in cif_files}
    for future in as_completed(future_to_cif): #Collect results
        cif_file = future_to_cif[future]
        try:
            name, structure, formula = future.result() #completed results
            if structure and formula: #If laoded successfully
                pymatgen_structures[name] = structure # Store the structure by file name
                formulas_to_files[formula].append(name)
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(cif_file)}: {e}")

# Query MP for structure matching each unique formula
mp_structures = {} #Store MP structures by formula
for formula in formulas_to_files.keys(): #loop through unique formulas
    try:
        print(f"\n🔎 Querying Materials Project for {formula}...")
        mp_structures[formula] = mpr.get_structures(formula) # Fetch all MP structures with this formula
    except Exception as e:
        print(f"❌ Error querying {formula}: {e}")
        mp_structures[formula] = None

# Track novelty and matching structures against MP project data
is_novel = {} # track if each structure is novel (true), existing (false) or unchecked
matched_structures = {}  # Store matches: {cif_file: matched_mp_formula}
error_files = [] # list the files with errors
for cif_file, local_structure in pymatgen_structures.items(): # Retrieve MP structures for this formula
    formula = local_structure.composition.alphabetical_formula
    try:
        existing_materials = mp_structures.get(formula)
        if existing_materials is None:
            is_novel[cif_file] = None
            error_files.append((cif_file, "MP query failed"))
        elif existing_materials: # If MP has structures for this formula
            match_found = False
            for mp_structure in existing_materials: # Compare with each MP structure
                if matcher.fit(local_structure, mp_structure): # Check structural similarity
                    match_found = True
                    matched_structures[cif_file] = mp_structure.composition.alphabetical_formula # Record the match
                    print(f"✅ {cif_file} matches MP structure: {mp_structure.composition.alphabetical_formula}")
                    break
            is_novel[cif_file] = not match_found # Novel if no match found
            if not match_found:
                print(f"❌ {cif_file} has no structural match in MP for {formula}")
        else: # No MP structures exist for this formula
            is_novel[cif_file] = True  # Mark as novel
            print(f"✅ {cif_file} is novel (no MP entries for {formula})")
    except Exception as e:
        print(f"❌ Error checking {cif_file}: {e}")
        is_novel[cif_file] = None
        error_files.append((cif_file, str(e)))

# Display the status of each structure
print("\n=== Structure Status ===")
novel_structures = [] # List to collect novel CIF files
for cif_file in sorted(is_novel.keys()):
    status = is_novel[cif_file]
    if status is True:
        novel_structures.append(cif_file) # Add to novel list
        print(f"{cif_file}: novel")
    elif status is False:
        print(f"{cif_file}: exists in MP (matched: {matched_structures[cif_file]})")
    else:
        print(f"{cif_file}: could not be checked")

# Print matching structures explicitly
if matched_structures:
    print("\n=== Matching Structures in Materials Project ===")
    for cif_file, matched_formula in matched_structures.items():
        print(f"{cif_file} → {matched_formula}")
else:
    print("\n❌ No matching structures found in Materials Project.")

# Calculate and print ratio
novel_count = sum(1 for status in is_novel.values() if status is True) # Count novel structures
total_checked = sum(1 for status in is_novel.values() if status is not None)# Count structures successfully checked
if total_checked > 0: # Calculate novelty ratio
    ratio = novel_count / total_checked
    print(f"\n=== Summary ===")
    print(f"Novel structures: {novel_count}/{total_checked} (Ratio: {ratio:.2%})") # Show count and percentage
    print(f"Matched structures: {len(matched_structures)}") # Number of matches
    print(f"Failed checks: {len(error_files)}")  # Number of errors
    if novel_structures:
        print("Novel CIF files:", ", ".join(novel_structures)) # List all novel files
    if error_files:
        print("Errors encountered:")
        for file, error in error_files:
            print(f"  {file}: {error}")
else:
    print("\n❌ No structures were successfully checked.")