# InVivo Atlas Files (v10.4)

This directory contains the files for the *InVivo* Atlas mouse brain required for anatomical segmentation using InVivoSegment.

## Atlas Specifications

- **Version**: 10.4
- **Species**: Mouse (Mus musculus)
- **Atlas Type**: Mn(II)-enhanced MRI
- **Number of Segments**: 116 distinct brain regions, separated into white matter, gray matter/subcortical nuclei, ventricles, and non-specified brain.
- **Voxel Labels**:

  - Label image: Integer values corresponding to segment index value. (1-116)
  - Grayscale image: Integer values between (0-256)

- **Data Format**: NIfTI-1 (.nii) format
- **Image Details**:
  - FOV =  11.60 mm x 15.84 mm x 7.84 mm
  - Matrix = 145 x 198 x 98 voxels
  - Orientation = Right-Left x Anterior-Posterior x Inferior-Superior
  - Resolution = 0.08 mm (80 micron) isotropic

## Files Overview

### Files Required for Segmentation (inverse alignment)

#### **InVivoAtlas_v10.4.nii**

- **Format**: NIfTI (Neuroimaging Informatics Technology Initiative)
- **Purpose**: Reference/parent atlas file for alignment and on which segment labels were drawn.
- **Description**: T<sub>1</sub>-weighted grayscale image of a living mouse brain with Mn(II)-enhancement at 80 micron (0.08 mm) isotropic resolution. The brain image has already been extracted from / stripped of non-brain tissue.
- **Usage**: Not directly used in InVivoSegment. However, this file is the template anatomical image used for alignment of the atlas label image (below) to a dataset. See example example alignment files in the GitHub repo for our paper ([Inverse Alignment Files](https://github.com/bearerlab/memri-processing-QA/tree/main/segmentation)) directory. We provide three different alignment procedures, from commonly used registration software ([ANTS](https://github.com/antsx/antspy), [FSL](https://fsl.fmrib.ox.ac.uk/fsl/docs/), and [SPM](https://www.fil.ion.ucl.ac.uk/spm/)). We adjusted the options/parameters  for inverse alignment of the **InVivo Atlas** to the minimal deformation target (MDT) from a Mn(II)-enhanced MRI dataset.

### Required Files for InVivoSegment

Please also see the [../examples/atlas/](../examples/atlas/) directory, which contains versions of these two files used in the segmentation examples.

These two files must match. Any changes made to the atlas must be reflected in the sorting/lookup table and vice versa.

#### **InVivoAtlas_Sort_v10.4.csv**

- **Format**: Comma-separated values (CSV)
- **Purpose**: Lookup table for atlas segment information
- **Description**: Contains metadata for all 116 brain segments, including:
  - `Index`: Numerical label corresponding to NIfTI voxel values
  - `SegmentName`: Full descriptive name of the brain region
  - `Abbr.Cleaned`: Standard abbreviation used in outputs and figures
  - `Grouping`: Hierarchical anatomical grouping identifier
  - `Domain`: Higher-level anatomical domain
- **Usage**: Load this file in the InVivoSegment GUI (Step 2: Load Atlas LUT)

#### **InVivoAtlas_labels_v10.4.nii**

- **Format**: NIfTI
- **Purpose**: Brain atlas label image used for segmentation.
- **Description**: High-resolution 3D brain atlas with 116 distinct anatomical segments. Each voxel contains an integer label corresponding to a specific brain region. Segments naming/organization are based on the Allen Institute's CCF3 and Paxinos-Franklin Mouse Brain Atlases. This file should be inversely aligned to dataset files by applying the warp fields generated from alignment of the grayscale image above.
- **Usage**: Load this file in the InVivoSegment GUI (Step 3: Load Atlas Labels NIfTI)
- **Note**: This is the **inversely aligned** version optimized for anatomical segmentation pipelines

### Reference Files

#### **invivoseg_v10.4.lut**

- **Format**: Lookup table (LUT)
- **Purpose**: Alternative segment definition file assigning RGB color values to segment names and index values in the CSV files above.
- **Description**: Custom lookup table format for use with other neuroimaging tools
- **Usage**: Used in software like FSLeyes for visualization of segment boundaries.

#### **InVivoAtlas_v10.4 - List of abbreviations Table.docx**

- **Format**: Microsoft Word document
- **Purpose**: To provide full segment names 
- **Description**: Detailed table with all 116 segment abbreviations, full names, and anatomical groupings
- **Usage**: Reference for segment names and identifiers when analyzing output data.

## Using These Files with InVivoSegment

1. **Place both required files in your atlas directory** (recommended: `examples/atlas/`)
2. **In the GUI, follow these steps**:
   - Step 2: Click "Load Atlas LUT" and select `InVivoAtlas_Sort_v10.4.csv`
   - Step 3: Click "Load Atlas Labels NIfTI" and select `InVivoAtlas_labels_v10.4.nii`
   - Step 4: Click "Generate Masks from Atlas" to create segment masks

## Segment Output

When you run segmentation in InVivoSegment, output files will use:

- **Segment Abbreviations** from the `Abbr.Cleaned` column
- **Grouping Information** for organizing and plotting results
- **Domain Classification** for higher-level anatomical grouping in visualizations

## Version Notes

This is **version 10.4** of the InVivo Atlas. Ensure all files in this directory are from the same version to maintain consistency and avoid segmentation errors.

If you have questions or encounter issues with these files, please refer to the main [README.md](../README.md) in the InVivoSegment repository.
