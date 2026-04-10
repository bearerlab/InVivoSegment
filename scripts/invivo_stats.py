# invivo_stats.py
"""
Processes selected NIfTI files via segmentation with statistical summaries
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Local utilities and loader used by this module
from .invivo_util import ensure_required_columns
from .invivo_loader import load_nifti_as_numpy

# Segmental Centroid and Weighted (by Intensities) Segmental Centroid
def centroid_3d(arr):
    """
    Compute centroid of 3D array; return (x,y,z) or None.
    
    Inputs:
    - arr: a 3D np.ndarray representing a segmental information from a NIfTI image, either from boolean InVivo atlas segment masks or masked intensity/statistic values. 
    """
    if not isinstance(arr, np.ndarray) or arr.size == 0:
        return None
    total = np.nansum(arr)
    if total == 0 or np.isnan(total):
        return None
    coords = np.argwhere(arr)
    if coords.size == 0:
        return None
    if arr.dtype == np.bool_ or np.all((arr == 0) | (arr == 1)):
        return tuple(coords.mean(axis=0).tolist())
    grid = np.indices(arr.shape).astype(np.float64)
    cx = np.nansum(grid[0] * arr) / total
    cy = np.nansum(grid[1] * arr) / total
    cz = np.nansum(grid[2] * arr) / total
    return (cx, cy, cz)

# Calculate segmental statistics  
def calculate_statistics(voxel_data: np.ndarray, mask: np.ndarray, stats_boolean: list, thr=None):
    """
    Compute requested statistics for voxels within mask > thr.
    stats_boolean order: [Mean, Median, StDev, Q1, Q3, Min, Max, ActVol, FAV, CoG]. This is the main workhorse function of the segmentation process.

    Inputs:
    - voxel_data: an np.ndarray of voxel-wise data from an NIfTI image. Statistics calculcated related to this image's intensities. 
    - mask: an np.ndarray corresponding to a particular atlas segment 
    - stats_boolean: boolean list of selected stats

    Outputs:
    - results: a dictionary containing values corresponding to the column/variable names (default and selected) for segmentation. 
    """
    if mask.shape != voxel_data.shape:
        raise ValueError("Mask and voxel_data must have same shape.")

    mask_bool = mask.astype(bool)
    seg_vol = float(np.nansum(mask_bool))
    results = {"SegVol": seg_vol}
    if seg_vol == 0:
        names = ["Mean", "Median", "StDev", "Q1", "Q3", "Min", "Max", "ActVol", "FAV"]
        for i, n in enumerate(names):
            if i < len(stats_boolean) and stats_boolean[i]:
                results[n] = 0
        results.update({"CoGx": 0, "CoGy": 0, "CoGz": 0, "sCoGx": 0, "sCoGy": 0, "sCoGz": 0})
        return results

    masked_vals = voxel_data[mask_bool]
    try:
        # thr parameter may be a string (from the GUI); convert to float if possible
        if thr is None or (isinstance(thr, float) and np.isneginf(thr)) or (str(thr).strip() == ""):
            thr_value = -np.inf
        else:
            thr_value = float(thr)
    except Exception:
        # No valid numeric threshold provided; use -inf so comparison includes all finite voxels
        thr_value = -np.inf
    above_thr = masked_vals > thr_value
    masked_thresholded_vals = masked_vals[above_thr]

    idx = 0
    if stats_boolean[idx]:
        results["Mean"] = round(float(np.nanmean(masked_thresholded_vals)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["Median"] = round(float(np.nanmedian(masked_thresholded_vals)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["StDev"] = round(float(np.nanstd(masked_thresholded_vals)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["Q1"] = round(float(np.nanquantile(masked_thresholded_vals, 0.25)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["Q3"] = round(float(np.nanquantile(masked_thresholded_vals, 0.75)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["Min"] = round(float(np.nanmin(masked_thresholded_vals)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["Max"] = round(float(np.nanmax(masked_thresholded_vals)) if masked_thresholded_vals.size > 0 else 0, 2)
    idx += 1
    if stats_boolean[idx]:
        results["ActVol"] = int(np.nansum(above_thr))
    idx += 1
    if stats_boolean[idx]:
        act = int(np.nansum(above_thr))
        results["FAV"] = round((act / seg_vol) if seg_vol > 0 else 0, 3)
    idx += 1
    if stats_boolean[idx]:
        base_cog = centroid_3d(mask.astype(float))
        if thr_value == -np.inf:
            thresh_cog = base_cog
        else:
            full_masked = voxel_data * mask_bool
            bool_masked_full = full_masked > thr_value
            thresh_weighted = full_masked * bool_masked_full
            thresh_cog = centroid_3d(thresh_weighted)
        if base_cog is None:
            results.update({"CoGx": 0, "CoGy": 0, "CoGz": 0})
        else:
            results["CoGx"], results["CoGy"], results["CoGz"] = [round(float(v), 2) for v in base_cog]
        if thresh_cog is None:
            results.update({"sCoGx": 0, "sCoGy": 0, "sCoGz": 0})
        else:
            results["sCoGx"], results["sCoGy"], results["sCoGz"] = [round(float(v), 2) for v in thresh_cog]
    return results

# Segment selected NIfTIs
def process_nifti_files(nifti_df: pd.DataFrame, 
                        masks_arr,
                        segment_lut: pd.DataFrame,
                        stats_boolean: list, progress_callback=None):
    """
    Summary: Process NIfTIs listed in nifti_df and compute requested stats for each mask in masks_arr.

    Input:
        - nifti_df: a pd.DataFrame listing the names of selected NIfTI files  
        - masks_arr: a np.array representing the NIfTI label image.
        - segment_lut: a pd.DataFrame of the processed Atlas LUT csv
        - stats_boolean: a boolean list from the GUI selection of segment statistics to calculate.
    Output:
        - results: a pd.DataFrame of segmentation results for each input given selected statistics.
    """
    ensure_required_columns(segment_lut, ["Index", "SegAbbr", "SegGroup", "Domain"])
    lut_map = {int(r): str(n) for r, n in zip(segment_lut["Index"], segment_lut["SegAbbr"])}
    lut_map_seggroup = {int(r): str(n) for r, n in zip(segment_lut["Index"], segment_lut["SegGroup"])}
    lut_map_domain = {int(r): str(n) for r, n in zip(segment_lut["Index"], segment_lut["Domain"])}
    seg_intensities = [k for k in masks_arr.keys() if k in lut_map and k > 0]
    total_jobs = len(nifti_df) * len(seg_intensities)
    processed = 0
    results = []
    if progress_callback:
        progress_callback(0, total_jobs, "Starting segmentation")
    for idx, row in nifti_df.iterrows():
        image_path = row["Image"]
        if not Path(image_path).exists():
            processed += len(seg_intensities)
            if progress_callback:
                progress_callback(processed, total_jobs, f"Image not found: {image_path} — skipping")
            continue
        try:
            voxel_data, aff, hdr = load_nifti_as_numpy(image_path)
        except Exception as e:
            processed += len(seg_intensities)
            if progress_callback:
                progress_callback(processed, total_jobs, f"Failed to load {image_path}: {e}")
            continue
        for intensity in seg_intensities:
            seg_name = lut_map.get(intensity)
            seg_group = lut_map_seggroup.get(intensity)
            seg_domain = lut_map_domain.get(intensity)
            if not seg_name:
                processed += 1
                continue
            mask = masks_arr[intensity]
            try:
                stats = calculate_statistics(voxel_data, mask, stats_boolean, thr=row.get("Threshold", None))
            except Exception:
                stats = {"SegVol": 0}
            results.append({
                "Image": Path(image_path).name,
                "Group": row.get("Group", ""),
                "Condition": row.get("Condition", ""),
                "SubID": row.get("SubID", ""),
                "Threshold": row.get("Threshold", None),
                "SegAbbr": seg_name,
                "Grouping": seg_group,
                "Domain": seg_domain,
                **stats
            })
            processed += 1
            if progress_callback:
                progress_callback(processed, total_jobs, f"Processed {Path(image_path).name} - {seg_name}")
    if progress_callback:
        progress_callback(processed, total_jobs, "Segmentation finished")
    return pd.DataFrame(results)