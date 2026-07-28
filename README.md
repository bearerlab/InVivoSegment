# InVivo Atlas Segmentation

A Python GUI application for anatomical segmentation of MRI brain images using the *InVivo* Mouse Brain Atlas.

*If you use or modify this atlas or the InVivoSegment code, please cite this repository (see "Cite this Repository" above) and the preprint listed below (DOI below).*

[![bioRxiv](https://img.shields.io/badge/bioRxiv-10.64898%2F2026.04.10.717774-red)](https://doi.org/10.64898/2026.04.10.717774)

## Overview

This software package performs anatomical segmentation of MR brain images using the *InVivo* Atlas (v10.4), a high-resolution Mn(II)-enhanced MRI of a mouse brain. The package provides an intuitive graphical user interface (GUI) for calculating summary statistics of image voxel intensities across 116 brain segments.

Although developed for longitudinal Mn(II)-enhanced MRI (MEMRI) data, the segmentation pipeline can be applied to any 3D brain images in NIfTI file format, including:

- Individual subject intensity images
- Group-level statistical maps (e.g., T-maps)
- Experimental condition data
- Validation datasets

## Features

- **Flexible Experimental Design**: Supports arbitrary combinations of groups and conditions
- **Multiple statistics**: Choose from 10 different segment-wise metrics (mean, median, standard deviation, quartiles, min/max, activation volumes, center-of-mass)
- **Threshold control**: Apply intensity or statistical thresholds to segmentation
- **Batch processing**: Process multiple images in a single analysis
- **Output management**: Automatically organized output directories with CSV results
- **User-friendly GUI**: Built with Tkinter for cross-platform compatibility

## Installation

### Requirements

- Python 3.8 or higher
- __Core Python Dependencies__: numpy, pandas, nibabel, matplotlib. Other packages are in the standard Python library.
- __Example.ipynb Dependencies__: jupyter (or notebook/jupyterlab) and python packages: scipy and seaborn. These are not required for the core segmentation application, but to run the notebook for validations. 

### Clone from GitHub

```bash
git clone https://github.com/bearerlab/InVivoSegment.git
cd InVivoSegment
```

### Run from Source

Simply run the main script to start the GUI:

```bash
python InVivoSegment.py
```

Or, for more information about command-line options:

```bash
python InVivoSegment.py -h
python InVivoSegment.py --mode info
python InVivoSegment.py --mode version
```

## Quick Start

1. **Launch the GUI**:

   ```bash
   python InVivoSegment.py
   ```

2. **Organize your data** following the structure described in the examples:
   - Create a working directory with subdirectories for InputData and atlas files
   - Place your NIfTI images in the InputData directory
   - Place the InVivo Atlas label image (NIfTI) and lookup table (CSV) in the atlas directory

3. **Use the GUI to**:
   - Select your working directory
   - Load the atlas lookup table and __aligned__ label image
   - Specify your experimental design (groups and conditions)
   - Choose statistics to compute
   - Apply any necessary thresholds
   - Run segmentation
   - Export results to CSV

## Example Workflow and Validation Datasets

This repository includes example data demonstrating:

- Multi-site validation datasets
- Noise simulation validation
- Analysis of statistical maps (SPM T-maps)
- Segmentation of intensity images across groups and conditions

See the [Examples.ipynb](./Examples.ipynb) notebook and `/examples` directory for detailed walkthroughs.

### Example Directory Organization

Organize your data hierarchically to facilitate systematic file selection within the GUI. An example of how we have organized our data is shown below. 

```
working_directory/
├── atlas/
│   ├── InVivoAtlas_labels_v10.4.nii          # Atlas label image aligned to your data
│   └── InVivoAtlas_Sort_v10.4.csv            # Atlas lookup table
├── intensities/
│   ├── InputData/
│   │   ├── Grp1Con1/
│   │   │   ├── Grp1_Con1_01.nii
│   │   │   └── ...
│   │   └── Grp1Con2/
│   │       └── ...
│   ├── Masks/                                 # Auto-generated
│   └── OutputData/                            # Auto-generated
│       └── CSVs/
└── statistical_maps/
    ├── InputData/
    │   └── spmT_Grp1_Con2gt1_P05-T181-C8.nii
    ├── Masks/                                 # Auto-generated
    └── OutputData/                            # Auto-generated
        └── CSVs/
```

**Naming conventions**:

- `Grp#`: Group identifier
- `Con#`: Condition/contrast identifier  
- `P#`: Voxel-wise significance threshold
- `T#`: T-value or effect-size threshold
- `C#`: Cluster-size threshold (voxels)

### GUI Workflow (8 Steps)

**Step 0 - Prepare Data**: Organize your input files following the directory structure above. Be sure to have an aligned atlas label image and sorting table. See [InVivoAtlas_files](./InVivoAtlas_files/) for raw files, and [./examples/atlas/](./examples/atlas/) for aligned labels used in examples.

**Step 1 - Select Output Directory**: Choose your working directory. The GUI automatically creates `Masks` and `OutputData` subdirectories.

**Step 2 - Load Atlas Lookup Table**: Select your atlas sorting table (CSV). This defines segment identities and labeling conventions.

**Step 3 - Load Atlas Label Image**: Select your InVivo Atlas label image (NIfTI). This must be spatially aligned to your input images.

**Step 4 - Generate Masks**: Create binary masks for individual atlas segments. Optionally save as compressed NIfTI files (`.nii.gz`).

**Step 5 - Specify Experimental Design**: Define your groups and conditions. The GUI validates consistency with your input data.

**Step 6 - Select Statistics**: Choose which metrics to compute:

- Mean, Median, Standard Deviation
- Quartiles (Q1, Q3), Min, Max
- Activation volume (number of suprathreshold voxels)
- Fractional activation volume (percentage of segment)
- Center-of-mass (unweighted and signal-weighted)

**Step 7 - Apply Thresholds (Optional)**: Set intensity or statistical thresholds. This value is retained as metadata in the output CSV.

**Step 8 - Run Segmentation**: Select your input images and run segmentation. Results are saved to CSV format in `OutputData/CSVs/`.

**Note on Paired/Longitudinal Data**: Images must be selected in consistent order across conditions to preserve subject alignment.


### Validating Your Installation

Before applying InVivoSegment to new data, we recommend confirming that your installation reproduces the reference results below by running the `python InVivoSegment.py` function on the data in the `test` directory. We focus here on the two examples used for quantitative validation in the associated paper. The validation folders in the `examples` directory have the original validated output that one could use for comparison.

**1. Multisite validation (simulated signal).**

Run `InVivoSegment.py` on `test/validation/InputData/MultisiteValidation.nii`, a single simulated image containing signal cubes in three segments (ACA, CP, PRN), as follows...

0. In a terminal window navigate to the package directory and run `python InVivoSegment.py`
1. Select the corresponding `test/validation/` directory as output, and then load the aligned atlas files from `test/atlas/` (`iwaInVivoAtlas_labels_v10.4.nii` and `InVivoAtlas_Sort_v10.4.csv`).
2. Generate masks, do not save masks for this validation
3. Setup design. A) 1 group and 1 condition; B) Use default labels and ensure n = 1 for number of images to be selected. Save design.
4. Select all segmentation measures check boxes. 
5. Apply an intensity threshold of `0` 
6. Run segmentation - selecting the `test/validation/InputData/MultisiteValidation.nii` input file. Name the CSV output from each run as: `ValidationResults_thr0.csv`
7. Repeat steps 5 and 6 twice, each time changing the threshold value {`1` or `2`} and CSV output filename {`ValidationResults_thr1.csv` or `ValidationResults_thr2.csv`}
8. Compare the resulting per-segment statistics against validated CSVs in `examples/validation/OutputData/CSVs` and against the manually computed reference values in `examples/validation/ValidationDataComparison.xlsx`.

You can also try running the first section of `Example.ipynb` using your newly generated data for futher validation.  

**2. Group-level statistical map (SPM T-map; corresponds to Fig. 7 in the associated paper).**

Repeat the process above but using the `test/statistical_tmap/` directory and SPM T-Map NIfTI file. In this case no thresholds are needed.

1. Using the same aligned atlas files, run `InVivoSegment.py` on the pre-thresholded T-map in `test/statistical_tmap/InputData/`.
2. Because significance thresholding is already applied upstream in SPM, no threshold value needs to be set in the GUI for this input type.
3. Compare the CSV output in `test/statistical_tmap/OutputData/CSVs/` against the values in `examples/statistical_tmap/OutputData/CSVs/SPMResults.csv` and reported in the associated paper.

`Examples.ipynb` automates both comparisons (and the corresponding column-graph summaries) if you would rather run them programmatically than by inspection. If your results reproduce the reference values above, you can proceed to your own data with confidence in the installation.

### Experimental Design Inputs Across Study Types

The **Experimental Design** step of the GUI (Step 5, below) is flexible enough to accommodate designs ranging from a single image to many subjects across multiple groups and conditions. The table below shows how the Groups/Conditions/images-per-cell inputs differ across the examples in this repository, to help you configure this step for your own data:

| Dataset type | Groups | Conditions | Images per group×condition (*n*) | Threshold |
|---|---|---|---|---|
| Multisite validation (single simulated image) | 1 | 1 | 1 | Set manually; run once per threshold (`>0`, `>1`, `>2`) |
| Single statistical map (e.g., one T-map contrast) | 1 | 1 | 1 (pre-thresholded map) | None — thresholding already applied upstream |
| Multiple within/between-group statistical maps | ≥1 per comparison | 1 contrast per map | 1 per contrast | None — each map pre-thresholded |
| Longitudinal/cross-sectional intensity images | e.g., 2 | e.g., 2+ (e.g., pre-/post-Mn(II)) | e.g., *n* = 11 per group×condition | Optional |

For paired or longitudinal designs with multiple images per subject, images must be selected in a consistent order across conditions in Step 8 to preserve subject alignment (see the Note under GUI Workflow, below).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Authors

- **Taylor W. Uselman** ([twuselman@salud.unm.edu](mailto:twuselman@salud.unm.edu))
- **Elaine L. Bearer** ([elaine.bearer@gmail.com](mailto:elaine.bearer@gmail.com)) - corresponding author

## Support

For issues, questions, or feature requests, please open an issue on GitHub: [Issues](https://github.com/bearererlab/InVivoSegment/issues)
