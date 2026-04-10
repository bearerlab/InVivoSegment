# invivo_plot.py
"""
Functions for plotting segmentation statistics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def matplotlib_columngraph(
    seg_df: pd.DataFrame,                  # Segment statistics to plot
    seg_rm: list = None,                   # Segments to remove from plot
    order: str = "Grouping",               # Anatomical grouping order
    # other options inclue "abc" or "magnitude" 
    y: str = "FAV",                        # Column for y-axis values
    fill: str = None,                      # Variable used for color grouping
    col_vals = ("#0000FF", "#E34234",  # Primary fill colors
                "#87CEEB", "#FFFF00"), # Secondary Fill colors
    diff: str = None,                      # What difference to compute
    save: bool = True,                     # Whether to save plot & CSV
    fname: str = None,                     # Output filename (no extension)
    fig_dims = (3.3, 1.1),                 # Figure dimensions (inches)
    font_scale = 1                         # Scalar multiplier to scale font size
):
    """
    Matplotlib translation of the ggplot_columngraph() function (fracvol_graph.R), from 'Code used in 'Reconfiguration of brain-wide activity after early life adversity.' See References.
    
    Input:
    - seg_df: a pd.DataFrame of segmentation statistics segmentation generated using InVivoSegment.py
    - seg_rm: list of segment abbreviations for segments to remove
    - order: string indicating the ordering scheme for column graph segments
    - y: the column/variable name in seg_df to plot
    - fill: the columne/variable name in seg_df to group pairwise plots by
    - col_vals: a list containing coloring scheme for column graphs in order of fill categories/levels
    - diff: string indicating whether to compute differences between conditions. Option include "diff" for difference (con2 - con1) or "fc" for fold change (100*(con2/con1 - 1)). Note: this will only work if there are exactly 2 conditions in the 'Condition' column of seg_df and if y is a numerical variable. Additionally, the resulting plot will only show the computed differences for the second condition (con2).
    - save: boolena for saving output plot
    - fname: filename string if save == True
    - fig_dims: width x height dimensions of the saved figure (in inches). 
    - fig_scale: scalar multiplier for font dimensions. This will likely be needed if fig_dims are changed. 
    
    Output:
    - column graph plot object
    - (optional) saved to 'fname' directory

    Notes: Current dims allows for approrimately 1 graph per column of a typical journal. Slight adjustment might be needed for appropriate sizing. Additionally, label/text sizes may need to be adjusted. This can be done on the matplotlib output object or by adjusting code below.   
    """
    # Validations
    if save and fname is None:
        raise ValueError("Need to specify file name (fname) if saving plot.")
    if seg_rm is not None and not isinstance(seg_rm, list):
        raise ValueError("The seg_rm option must be a list, e.g., seg_rm = ['seg1','seg2']")
    if (y is None) or (y not in seg_df.columns):
        raise ValueError("Need to specify numerical variable to plot on 'y' axis")
    if (fill is not None) and (fill not in seg_df.columns):
        raise ValueError("Need to specify variable that is in seg_df for 'fill'")
    

    if (fill is None):
        print("place holder")
    else:
        # Domain Order
        domain_order = ["OLF", "CTX", "HIP", "AMY", "STR/PAL", "THA", "HYP", "MB", "HB", "CB", "WM", "V", "WB"]
        seg_df = seg_df.copy()
        seg_df['Domain'] = pd.Categorical(seg_df['Domain'], categories=domain_order, ordered=True)
        # Remove any segments if provided
        if seg_rm is not None and seg_df['SegAbbr'].isin(seg_rm).any():
            seg_df = seg_df[~seg_df['SegAbbr'].isin(seg_rm)].reset_index(drop=True)

        # Order Segments and Domains
        if order == "Grouping":
            # Sort segments by InVivo Atlas anatomical grouping
            seggroup_order = sorted(seg_df['Grouping'].unique().tolist())
            value_map = seg_df.set_index('Grouping')['SegAbbr'].to_dict()
            ordered_values = pd.Series(seggroup_order).map(value_map)
            # Reorder categories
            seg_df['SegAbbr'] = pd.Categorical(seg_df['SegAbbr'], categories= ordered_values, ordered=True)

            seg_df = seg_df.sort_values("Grouping", ascending=True)
            
            # Check for numbers of individuals
            if len(seg_df["SubID"].unique()) > 1:
                
                if diff is not None and (diff == "diff" or diff == "fc") and (y != "SegVol"):
                    
                    seg_df[y] = pd.to_numeric(seg_df[y], errors='coerce')
                    valid_values = seg_df[y].notna() & (seg_df[y] > 0)

                    
                    # Pivot to wide format: one row per (SubID, SegAbbr), columns for each condition
                    pivoted = seg_df.pivot_table(index=['SubID', 'SegAbbr'], columns='Condition', values=y, observed=True)
                    con1 = sorted(seg_df['Condition'].unique())[0]
                    con2 = sorted(seg_df['Condition'].unique())[1]
                    
                    if diff == "diff" and valid_values.all():
                        y = 'delta(' + y + ')'
                        # Calculate difference: con2 - con1
                        pivoted[y] = pivoted[con2] - pivoted[con1]

                        # Merge back to original DataFrame (optional)
                        seg_df = seg_df.merge(pivoted[y], on=['SubID', 'SegAbbr'])
                        seg_df = seg_df[seg_df['Condition'] == con2]
                        seg_df.reset_index(drop=True)

                    if diff == "fc" and valid_values.all():
                        y = 'FC(' + y + ')%'
                        # Calculate fold change: con2 / con1
                        pivoted[y] = 100*(pivoted[con2] / pivoted[con1] - 1)

                        # Merge back to original DataFrame (optional)
                        seg_df = seg_df.merge(pivoted[y], on=['SubID', 'SegAbbr'])
                        seg_df = seg_df[seg_df['Condition'] == con2]
                        seg_df.reset_index(drop=True)

                seg_df = seg_df.groupby(["Group","Condition","SegAbbr","Domain","Grouping"], observed=True, as_index=False)[y].agg(["mean", "std"]).rename(columns={"mean": y, "std": (y + "_sd")})
                


            # Group by the fill column and anatomical domain
            grouped = seg_df.groupby([fill, "Domain"], observed=True).size().reset_index(name="cnt")
            # Count the number of anatomical domains
            first_test = seg_df[fill].unique()[0]
            # Subset group
            grouped = grouped[(grouped[fill] == first_test)]
            # Create vector of segment corresponding  
            xcnt = grouped["cnt"].values
            # Compute x-positions for domain background rectangles
            xvals = [0.5]
            for i in range(1, len(xcnt)):
                xvals.append(xvals[i-1] + xcnt[i-1])

            xvals.append(xvals[-1] + xcnt[-1])
            # Alternating background colors
            bckgrnd_col = ["white" if i % 2 == 0 else "#404040" for i in range(len(xcnt))]
            # Domain annotation positions
            annotation_locations = [((xvals[i] + xvals[i+1]) / 2) - 1 for i in range(len(xcnt))]

            # Determine y-axis limits and ticks
            if y == "FAV":
                if (diff == "diff" or diff == "fc"):
                    ymax1 = np.ceil(seg_df[y].max())
                    ymin = min(0,np.floor(seg_df[y].min()))
                    ylinpos = ymin
                    ymin1 = ymin - (0.15 * max(abs(ymin),abs(ymax1)))
                    bks = np.linspace(ymin, ymax1, 5)
                    lms = (ymin1, ymax1)
                    ylabpos = 0.6*ymin1 + 0.4*ymin 
                else:
                    ymax1 = 1.0
                    ymin1 = 0.0
                    ylinpos = ymin1
                    bks = np.arange(ymin1, 1.25, 0.25)
                    lms = (-0.15, 1.0)
                    ylabpos = -0.075
            elif y == "SegVol":
                seg_df["SegVol (log10)"] = np.log10(seg_df[y])
                y = "SegVol (log10)"
                ymax1 = np.ceil(seg_df[y].max())
                ymin1 = 0.0
                ylinpos = ymin1
                bks = np.linspace(ymin1, ymax1, 5)
                lms = (-0.15 * ymax1, ymax1)
                ylabpos = 0.6*lms[0] + 0.4*ymin1 
            else:
                ymax1 = np.ceil(seg_df[y].max())
                ymin = min(0,np.floor(seg_df[y].min()))
                ylinpos = ymin
                ymin1 = ymin - (0.15 * max(abs(ymin),abs(ymax1)))
                bks = np.linspace(ymin, ymax1, 5)
                lms = (ymin1, ymax1)
                ylabpos = 0.6*ymin1 + 0.4*ymin 

            # --- Start Plot ---
            fig, ax = plt.subplots(figsize=fig_dims)

            # Draw alternating domain background rectangles
            for i in range(len(xcnt)):
                ax.axvspan(xvals[i]-1, xvals[i+1]-1, ymin=ymin1, ymax=ymax1, color=bckgrnd_col[i], alpha=0.1)

            # Plot bar graph (grouped by fill variable)
            unique_fills = seg_df[fill].unique()
            fill_colors = dict(zip(unique_fills, col_vals[:len(unique_fills)]))

            nsegs = len(seg_df[seg_df[fill] == seg_df[fill].unique()[0]]["SegAbbr"].astype(str).tolist())
            x = np.arange(nsegs)

            bar_width = 0.5 / len(unique_fills)
            for i, fval in enumerate(unique_fills):
                subset = seg_df[seg_df[fill] == fval]
                ax.bar(
                    x + i * bar_width - (bar_width * len(unique_fills) / 2),
                    subset[y],
                    width=bar_width,
                    align = 'center',
                    color=fill_colors[fval],
                    label=fval
                )

            # Axis customizations
            ax.set_xlim(-1.5, nsegs - 0.5)
            ax.set_ylim(lms)
            ax.set_xticks([])
            ax.set_yticks(bks)
            ax.set_yticklabels([f"{b:.2f}" for b in bks], fontsize=4*font_scale)
            ax.axhline(0, color="black", linewidth=1.5)

            # Domain labels below x-axis
            for i, label in enumerate(grouped["Domain"].astype(str).tolist()):
                if (i == 0):
                    annotation_locations[i] = annotation_locations[i]
                if (i == len(grouped["Domain"].astype(str).tolist()) - 1):
                    annotation_locations[i] = annotation_locations[i]
                ax.text(annotation_locations[i], ylabpos, label, ha="center", va="center", fontsize=4*font_scale)
            
            # Add line at ymin + 15%
            if ylinpos != 0:
                plt.axhline(y=ylinpos, color='black', linestyle='-', linewidth=1.5)

            # Simplified theme equivalent
            ax.tick_params(bottom=False, left=True)
            ax.legend().set_visible(False)

            # Layout & title
            ax.set_xlabel("")
            ax.set_ylabel(y, fontsize=5*font_scale)
            ax.set_title("")

            # ax.invert_xaxis() 
            plt.tight_layout()

        elif order == "abc":
            # Sort segments alphabetically
            ordered_segs = sorted(seg_df['SegAbbr'].unique().tolist())
            # Reorder categories
            seg_df['SegAbbr'] = pd.Categorical(seg_df['SegAbbr'], categories=ordered_segs, ordered=True)

        elif order == "magnitude":
            # Compute max magnitude of y to order
            ordered_segs = seg_df[y].max().sort_values(ascending=False).index
            # Reorder categories
            seg_df['Category'] = pd.Categorical(seg_df['SegAbbr'],categories=ordered_segs, ordered=True)

        else:
            raise ValueError("'order' must be one of 'Grouping', 'abc', or 'magnitude'.")
        
    if save:
        if not os.path.isdir(os.path.dirname(fname)):
            raise ValueError(f"'{fname}' directory does not exist")
        else:
            if os.path.splitext(fname)[1] == "png":
                print("Testing... plot should be saved")
                plt.savefig(fname, dpi=300)         # PNG
            elif os.path.splitext(fname)[1] != "tiff" or os.path.splitext(fname)[1] != "tif":
                plt.savefig(fname, dpi=300)        # TIFF
            elif os.path.splitext(fname)[1] != "svg":
                plt.savefig(fname)                  # SVG
            elif os.path.splitext(fname)[1] != "eps":
                plt.savefig(fname)                  # EPS
            else:
                raise ValueError(f"'{os.path.splitext(fname)[1]}'extension not supported")
                
    return fig, ax
            