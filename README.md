Materials Structure Matching and Novelty Analysis

Overview

This project utilizes the pymatgen library to process CIF (Crystallographic Information File) structures, extract chemical formulas, and compare them against existing materials in the Materials Project database. The primary objectives of this project include:

Matching structures found in CIF files with those in the Materials Project database.

Identifying novel structures that do not exist in the database.

Analyzing and reporting on the materials dataset using advanced structure matching techniques.

Calculating ratios of novel vs. known materials for research insights.

Files and Functionality

1. results_param.py

Purpose

This script processes a collection of CIF files, extracts their chemical compositions, and attempts to match them with known structures in the Materials Project database using StructureMatcher.

Key Features

Reads up to 128 CIF files from a specified folder.

Uses pymatgen to parse CIF files and extract chemical formulas in alphabetical order.

Connects to the Materials Project API using an API key to query structures.

Utilizes StructureMatcher with specific comparison parameters:

Lattice tolerance: ltol=0.2 (adjusts for minor deviations in lattice parameters).

Site tolerance: stol=0.3 (allows for atomic position variations).

Angle tolerance: 5.0 degrees.

Primitive cell comparison, scaling enabled, and order-disorder comparator.

Compares each local structure to all retrieved structures from Materials Project.

Outputs whether a match is found or not for each CIF file.

Provides an overview of extracted formulas for verification.

How to Use

Run the script in a Python environment:

python results_param.py

Ensure that the CIF folder path is correctly set before execution.

2. results.py

Purpose

This script is similar to results_param.py but is designed for quick verification by processing only the first three CIF files.

Key Features

Processes up to 3 CIF files instead of 128.

Extracts chemical formulas and queries the Materials Project database.

Uses a default StructureMatcher configuration for comparison.

Instead of comparing with all retrieved structures, it matches against the first found structure.

Outputs matching results in a concise format.

How to Use

python results.py

Modify the CIF folder path inside the script before running.

3. novel.py

Purpose

This script determines the novelty of materials structures by checking whether they exist in the Materials Project database.

Key Features

Processes all CIF files found in the given folder.

Uses a fine-tuned StructureMatcher with the same tolerance values as results_param.py.

Tracks whether a structure exists in the Materials Project or is novel.

Classifies each CIF file into:

Novel Structure (not found in Materials Project).

Existing Structure (found in Materials Project and matched).

Unknown (query error or API limitation).

Calculates and displays the ratio of novel structures in the dataset.

Output Format

The script prints:

Structure Status:
file1.cif: novel
file2.cif: exists in MP
file3.cif: could not be checked

Overall ratio of novel structures: 67% (10/15)

How to Use

python novel.py

Ensure that the CIF file directory is correctly configured.

Dependencies

Make sure you have the required Python packages installed:

pip install pymatgen

API Key Requirement

To query the Materials Project API, you need to set up an API key:

Register at Materials Project.

Retrieve your API Key from your account settings.

Replace the placeholder MATERIALS_PROJECT_API_KEY in each script with your actual key.

Expected Output

Depending on the script executed, the expected results include:

The number of CIF files processed.

Extracted chemical formulas.

Match results for each structure against the Materials Project database.

Novelty assessment and ratio calculations (for novel.py).

Notes

Ensure the CIF folder path is correctly set in each script before execution.

The API key must be valid for queries to work properly.

Adjust parameters in StructureMatcher to fine-tune the comparison criteria.

Some structures might be similar but not identical; StructureMatcher helps detect minor variations.

License

This project is for research and educational purposes only.

Author

Leon Tang

For any issues or inquiries, feel free to reach out.

