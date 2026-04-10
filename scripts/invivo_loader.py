# invivo_loader.py
"""
Load InVivo Atlas files (CSV lookup table and NIfTI label image) and generate segment masks.
"""

import pandas as pd
import numpy as np
import nibabel as nib

# For loading atlas label NIfTI
def load_nifti_as_numpy(nifti_path):
    """Load NIfTI and return numpy array (float32), affine, header."""
    img = nib.load(str(nifti_path))
    voxel_data = img.get_fdata().astype(np.float32)
    return voxel_data, img.affine, img.header

# Generate masks
def generate_masks(atlas_data: dict,
                   lut_df,
                   save_dir,
                   save_masks = False):
    """
    Return masks only for indices present in lut_abbr and atlas.
    
    Inputs:
    - atlas_data: NIfTI atlas labels 
    - lut_df: CSV atlas pd.Dataframe
    - save_dir: Directory to save masks
    - save_masks: Boolean input from GUI on whether to save masks as NIfTIs 

    Outputs:
    -  masks: an np.Array containing segment masks
    - if save_masks: saved mask NIfTIs  
    """
    masks = {}
    # Validation of lut_df
    if lut_df is None or not isinstance(lut_df, pd.DataFrame) or lut_df.empty:
        raise ValueError("LUT DataFrame is required")
    # Obtain Indices and Abbreviations
    lut_indices = lut_df["Index"].astype(int).unique()
    lut_abbr = lut_df["SegAbbr"].astype(str)
    # Main loop to assign LUT info to masks
    for idx in range(len(lut_indices)):
        segabbr = lut_abbr[idx]
        indexval = lut_indices[idx]
        masks[int(indexval)] = (atlas_data["data"] == indexval).astype(np.uint8)
        # Save masks as NIfTIs
        if save_masks:
            if not save_dir.exists():
                raise FileNotFoundError(f"Save directory does not exist:{save_dir}")
            else:
                mask_img = nib.Nifti1Image(masks[int(indexval)],
                                            affine=atlas_data["affine"],
                                            header=atlas_data["header"])
                nib.save(mask_img, save_dir / f"{segabbr}_mask.nii.gz") 
    return masks