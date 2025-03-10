import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher, OrderDisorderElementComparator
from pymatgen.ext.matproj import MPRester
from pymatgen.io.ase import AseAtomsAdaptor

# ASE imports
from ase.calculators.emt import EMT
from ase.calculators.lj import LennardJones
from ase.calculators.dftb import Dftb
from ase.optimize import BFGS
from ase import Atoms

###############################################################################
# CONFIGURATION
###############################################################################
MATERIALS_PROJECT_API_KEY = "H0XbrfDs0BYaDbuGHkj56BaRhGeqbz9T"

# Paths to folders containing CIF files:
cif_folders = [
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\2.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\3.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\4.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\5.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\6.0",
    r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\7.0"
    # add more as needed...
]

# Choose calculator: 'emt', 'lj', 'dftb', or add your own
SELECTED_CALCULATOR = 'emt'  # Change this to 'lj' or 'dftb' as needed

# Define available calculators
CALCULATORS = {
    'emt': lambda: EMT(),
    'lj': lambda: LennardJones(sigma=3.4, epsilon=0.0103),  # Simple LJ potential (e.g., for noble gases)
    'dftb': lambda: Dftb(label='relax', kpts=(1, 1, 1)),  # DFTB+ (requires `ase-dftb` installed)
    # Add more here if you have them installed, e.g.:
    # 'lammps': lambda: LAMMPSlib(lmpcmds=["pair_style lj/cut 10.0"], ...),
    # 'vasp': lambda: VASP(xc='PBE', ...),
}

# StructureMatcher for novelty/uniqueness checks
matcher = StructureMatcher(
    ltol=0.2,
    stol=0.3,
    angle_tol=5.0,
    primitive_cell=True,
    scale=True,
    comparator=OrderDisorderElementComparator(),
    attempt_supercell=True,
    allow_subset=True,
)

###############################################################################
# STEP 1: COLLECT ALL CIF FILES
###############################################################################
cif_files = []
for folder in cif_folders:
    if os.path.exists(folder):
        for fname in os.listdir(folder):
            if fname.lower().endswith(".cif"):
                cif_files.append(os.path.join(folder, fname))
    else:
        print(f"❌ Error: Folder '{folder}' does not exist!")

if not cif_files:
    print("❌ Error: No CIF files found. Exiting.")
    raise SystemExit

print(f"📂 Found {len(cif_files)} CIF files. Processing...")


###############################################################################
# STEP 2: PARSE EACH CIF INTO A PYMATGEN STRUCTURE
###############################################################################
def read_cif_file(cif_file):
    """Reads a single CIF into a pymatgen Structure."""
    try:
        struct = Structure.from_file(cif_file)
        formula = struct.composition.alphabetical_formula
        return os.path.basename(cif_file), struct, formula
    except Exception as e:
        return os.path.basename(cif_file), None, None


pymatgen_structures = {}
formulas_to_files = defaultdict(list)

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = {executor.submit(read_cif_file, f): f for f in cif_files}
    for future in as_completed(futures):
        filename, structure, formula = future.result()
        if structure and formula:
            pymatgen_structures[filename] = structure
            formulas_to_files[formula].append(filename)

print(f"✅ Successfully parsed {len(pymatgen_structures)} structures "
      f"out of {len(cif_files)} files.")

###############################################################################
# STEP 3: NOVELTY CHECK vs. MATERIALS PROJECT
###############################################################################
mpr = MPRester(MATERIALS_PROJECT_API_KEY)
mp_structures_dict = {}

for formula in formulas_to_files:
    try:
        mp_structures_dict[formula] = mpr.get_structures(formula)
    except Exception as e:
        mp_structures_dict[formula] = []
        print(f"❌ MP query failed for formula {formula}: {e}")

is_novel = {}
matched_structures = {}

for cif_file, local_struc in pymatgen_structures.items():
    formula = local_struc.composition.alphabetical_formula
    known_mp_structs = mp_structures_dict.get(formula, [])

    if not known_mp_structs:
        # No matches in MP => automatically "novel"
        is_novel[cif_file] = True
    else:
        match_found = any(matcher.fit(local_struc, mp_s) for mp_s in known_mp_structs)
        is_novel[cif_file] = not match_found
        if match_found:
            matched_structures[cif_file] = formula

###############################################################################
# STEP 4: UNIQUENESS AMONG LOCAL STRUCTURES (AS-GENERATED)
###############################################################################
unique_groups = []
for cif_file, s in pymatgen_structures.items():
    found_group = None
    for group in unique_groups:
        if any(matcher.fit(s, grp_s) for _, grp_s in group):
            found_group = group
            break
    if found_group:
        found_group.append((cif_file, s))
    else:
        unique_groups.append([(cif_file, s)])

num_unique = len(unique_groups)
print(f"\n🔎 Among {len(pymatgen_structures)} local structures, "
      f"found {num_unique} unique groups.")


###############################################################################
# STEP 5: RELAX USING ASE with SELECTED CALCULATOR
###############################################################################
def relax_structure_ase(pmg_structure, calculator_name='emt', fmax=0.01):
    """
    Relax a pymatgen Structure using ASE with the selected calculator.

    Args:
        pmg_structure (Structure): The structure to relax.
        calculator_name (str): Name of the calculator to use ('emt', 'lj', 'dftb', etc.).
        fmax (float): Force convergence criterion (eV/Å).

    Returns:
        initial_energy (float): Initial total energy (in eV).
        final_structure (Structure): The relaxed structure.
        final_energy (float): Final total energy (in eV).
    """
    # Convert pymatgen Structure to ASE Atoms
    atoms = AseAtomsAdaptor.get_atoms(pmg_structure)

    # Set the calculator
    if calculator_name not in CALCULATORS:
        raise ValueError(f"Calculator '{calculator_name}' not recognized!")
    try:
        atoms.calc = CALCULATORS[calculator_name]()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize calculator '{calculator_name}': {e}")

    # Get initial energy
    try:
        initial_energy = atoms.get_potential_energy()  # eV
    except Exception as e:
        raise RuntimeError(f"Initial energy calculation failed with '{calculator_name}': {e}")

    # Relax the structure using BFGS
    try:
        optimizer = BFGS(atoms)
        optimizer.run(fmax=fmax)  # Relax until forces are below fmax
    except Exception as e:
        raise RuntimeError(f"Relaxation failed with '{calculator_name}': {e}")

    # Get final energy
    final_energy = atoms.get_potential_energy()  # eV

    # Convert back to pymatgen Structure
    final_structure = AseAtomsAdaptor.get_structure(atoms)

    return initial_energy, final_structure, final_energy


energy_differences = {}
relaxed_structures = {}
failed_relaxations = []

for cif_file, struct in pymatgen_structures.items():
    n_atoms = len(struct)
    if n_atoms == 0:
        failed_relaxations.append(cif_file)
        continue

    try:
        init_energy_eV, final_struct, final_energy_eV = relax_structure_ase(
            struct, calculator_name=SELECTED_CALCULATOR, fmax=0.01
        )
        relaxed_structures[cif_file] = final_struct

        # Convert difference to meV/atom
        diff_meV_per_atom = (final_energy_eV - init_energy_eV) * 1000.0 / n_atoms
        energy_differences[cif_file] = diff_meV_per_atom

    except Exception as e:
        print(f"❌ Error relaxing {cif_file} with {SELECTED_CALCULATOR}: {e}")
        failed_relaxations.append(cif_file)

###############################################################################
# STEP 6: PRINT SUMMARY
###############################################################################
total_structs = len(pymatgen_structures)
novel_count = sum(1 for k in is_novel if is_novel[k])
matched_count = len(matched_structures)
valid_relaxations = len(energy_differences)

print("\n=== SUMMARY ===")
print(f"Selected calculator: {SELECTED_CALCULATOR}")
print(f"Total CIF files read: {len(cif_files)}")
print(f"Total valid structures parsed: {total_structs}")
print(f"Novel structures vs. MP: {novel_count} / {total_structs} "
      f"({(novel_count / total_structs) * 100:.1f}%)")
print(f"Matched (non-novel) structures vs. MP: {matched_count}")
print(f"Unique local structure groups: {num_unique}")
print(f"Successful relaxations: {valid_relaxations} / {total_structs}")
print(f"Failed relaxations: {len(failed_relaxations)} => {failed_relaxations}")

over_20_mev = sum(1 for diff in energy_differences.values() if diff > 20.0)
print(f"Structures with energy diff > 20 meV/atom: {over_20_mev}")

if novel_count:
    print("\nNovel structures (no match in MP):")
    for cif_file, nov in is_novel.items():
        if nov:
            print(f"  - {cif_file}")

if over_20_mev:
    print("\nStructures with > 20 meV/atom difference:")
    for cif_file, diff in energy_differences.items():
        if diff > 20.0:
            print(f"  - {cif_file}: {diff:.1f} meV/atom")

print("\nDone.")