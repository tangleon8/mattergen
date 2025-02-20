# CIF File Processor and Materials Project Matcher

This Python script processes CIF (Crystallographic Information File) files, extracts their chemical formulas, and queries the Materials Project database to find matching structures. It uses the `pymatgen` library for structure manipulation and analysis.

## Prerequisites

Before running the script, ensure you have the following:

1. **Python 3.x** installed on your system.
2. **Pymatgen** library installed. You can install it using pip:
   ```bash
   pip install pymatgen
   ```
3. An **API key** from the [Materials Project](https://materialsproject.org/). Replace `"API"` in the script with your actual API key.

## Script Overview

The script performs the following tasks:

1. **Load CIF Files**: Reads CIF files from a specified folder.
2. **Extract Chemical Formulas**: Extracts the chemical formulas from the CIF files.
3. **Query Materials Project**: Searches the Materials Project database for structures matching the extracted formulas.
4. **Output Results**: Prints the matching structures found in the Materials Project.

## Usage

1. **Set the CIF Folder Path**: Modify the `cif_folder` variable to point to the folder containing your CIF files.
   ```python
   cif_folder = r"C:\Users\Leon\Downloads\UW-Madison-25\tmp_results\7.0"
   ```

2. **Set the Materials Project API Key**: Replace `"API"` with your actual Materials Project API key.
   ```python
   MATERIALS_PROJECT_API_KEY = "API"
   ```

3. **Run the Script**: Execute the script in your Python environment.
   ```bash
   python script_name.py
   ```

## Script Details

### Key Variables

- `cif_folder`: Path to the folder containing CIF files.
- `MATERIALS_PROJECT_API_KEY`: Your Materials Project API key.
- `cif_files`: List of CIF files in the specified folder.
- `pymatgen_structures`: Dictionary to store loaded structures.
- `extracted_formulas`: List to store extracted chemical formulas.
- `matched_results`: Dictionary to store matching results from the Materials Project.

### Functions

- **Structure.from_file(file_path)**: Loads a structure from a CIF file.
- **structure.composition.alphabetical_formula**: Extracts the chemical formula in alphabetical order.
- **mpr.get_structures(formula)**: Queries the Materials Project for structures matching the given formula.

### Error Handling

- The script checks if the specified folder exists and contains CIF files.
- It handles exceptions during file loading and Materials Project queries, printing error messages as needed.

## Example Output

```
📂 Found 128 CIF files. Processing the first 3...
📖 Reading file1.cif...
✅ Successfully loaded file1.cif | Extracted Formula: Al2O3
📖 Reading file2.cif...
✅ Successfully loaded file2.cif | Extracted Formula: SiO2
📖 Reading file3.cif...
✅ Successfully loaded file3.cif | Extracted Formula: NaCl

🔍 Extracted formulas for lookup: ['Al2O3', 'SiO2', 'NaCl']

🔎 Searching for: Al2O3 in Materials Project...
✅ Match found for Al2O3
🔎 Searching for: SiO2 in Materials Project...
✅ Match found for SiO2
🔎 Searching for: NaCl in Materials Project...
✅ Match found for NaCl

✅ Matching structures found in Materials Project:
Al2O3 → Al2O3
SiO2 → SiO2
NaCl → NaCl
```

## Notes

- The script processes the first 128 CIF files by default. You can modify the range in the loop to process more or fewer files.
- Ensure your API key has sufficient permissions to query the Materials Project database.

## License

This script is provided under the MIT License. Feel free to modify and distribute it as needed.

---

For any issues or questions, please refer to the [Pymatgen documentation](https://pymatgen.org/) or contact the script author.
