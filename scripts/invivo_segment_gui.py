# invivo_segment_gui.py
"""
Graphic User Interface for Segmentation Procedure
"""

import os, threading, ctypes, traceback
import numpy as np
import pandas as pd
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font

# Segmentation Package Functions
from .invivo_util import safe_read_csv
from .invivo_loader import load_nifti_as_numpy, generate_masks
from .invivo_stats import process_nifti_files

# GUI 
class SegmentationApp:
    """
    Main GUI class for segmentation, graphing, and export.

    Key behavior / constraints:
      - User must load Atlas LUT (CSV) and Atlas Labels (NIfTI).
      - User must click "Generate Masks from Atlas" to create `self.masks` before running segmentation.
      - User must create Group/Condition name fields (dynamic UI) and set N-values for each Group x Condition.
      - When Run Segmentation is clicked, the app prompts for the NIfTI files for each Group×Condition
        (grouped prompt per combination), constructs a single images DataFrame (one row per image),
        then calls process_nifti_files(...) once to compute all segment statistics and returns a single
        concatenated summary DataFrame which is saved by the user.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("InVivo Atlas Segmentation")
        # Data placeholders
        self.lut_df = None                # pandas DataFrame of LUT CSV
        self.atlas_nifti = None           # dict with keys: data, affine, header, path
        self.masks = None                 # dict of masks keyed by integer label (created by Generate Masks)
        self.output_df = None             # images DataFrame (one row per image; used as input to processing)
        self.summary_df = None            # final segmentation result (one row per segment per image)
        self.save_masks = False

        self.stat_vars = []
        self.stat_names = [
            "Mean", "Median", "Standard Deviation",
            "Quartile 1", "Quartile 3",
            "Minimum", "Maximum", "Segment Activation Volume",
            "Fractional Activation Volume", "Segment Center of Mass"
        ]
        self.directories = None
        self.odir_lbl = None
        self._build_ui()
    # -----------------------------
    # Scale
    # -----------------------------
    def make_dpi_aware(self):
        try:
            # Windows 8.1 and newer
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            scale_value = 1.0
        except AttributeError:
            try:
                # Windows 8.0 and older
                ctypes.windll.user32.SetProcessDPIAware()
                scale_value = 1.0
            except AttributeError:
                # Not Windows or very old Windows, no action needed
                scale_value = 1.645
                pass
        return scale_value
    # -----------------------------
    # UI builder (kept similar to prior)
    # -----------------------------
    def _build_ui(self):
        """
        Build the main GUI layout with:
          - Atlas LUT and Atlas NIfTI loaders
          - Dynamic Group/Condition controls (created earlier)
          - Generate Masks button (must be clicked before segmentation)
          - Run Segmentation button
          - Plotting controls and status/progress widgets
        """
        scale_value = self.make_dpi_aware()

        style = ttk.Style()

        frm = ttk.Frame(self.root, padding=8)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(1, weight=1)

        ar_font_s = font.Font(family = 'Arial', size = np.ceil(11*scale_value).astype(int), weight = 'normal')
        ar_font_b = font.Font(family = 'Arial', size = np.ceil(12*scale_value).astype(int), weight = 'bold')
        style.configure('Bold.TButton' , font = ar_font_b, fieldbackground="white")
        style.configure('Custom.TButton', font = ar_font_b, background ='blue', foreground='blue')
        style.configure('Bold.TLabel'     , font = ar_font_b)
        style.configure('Bold.TLabelframe', font = ar_font_b)
        style.configure('TButton', font = ar_font_s)
        style.configure('TLabel' , font = ar_font_s)
        style.configure('Custom1.TLabel' , font = ar_font_s, background="white")
        style.configure('Custom2.TLabel' , font = ar_font_b, foreground="limegreen")
        style.configure('TEntry' , font = ar_font_b, fieldbackground="white")
        style.configure("TCheckbutton", foreground="black", font=("Arial", np.ceil(11*scale_value).astype(int)), padding=5)
        
        # Select Output Directory
        ttk.Button(frm, text="Step 1: Select Output Directory", command=self.select_save_directory, style = 'Bold.TButton').grid(row=0, column=0, sticky="ew", pady=(0,6))
        ttk.Label(frm, text=f"Output Directory:", style = 'TLabel').grid(row=0, column=1, sticky="e", pady=(0,6))
        self.odir_lbl = ttk.Label(frm, text="(none)", style = 'Custom1.TLabel')
        self.odir_lbl.grid(row=0, column=2, sticky="w", pady=(0,6))

        # Atlas LUT and NIfTI selectors
        ## LUT
        ttk.Button(frm, text="Step 2: Load Atlas LUT", command=self.load_atlas_csv, style = 'Bold.TButton').grid(row=1, column=0, sticky="ew", pady=(0,6))
        ttk.Label(frm, text="Atlas LUT CSV:", style = 'TLabel').grid(row=1, column=1, sticky="e", pady=(0,6))
        self.atlas_lbl = ttk.Label(frm, text="(none)", style = 'Custom1.TLabel')
        self.atlas_lbl.grid(row=1, column=2, sticky="w", pady=(0,6))
        ## NIfTI
        ttk.Button(frm, text="Step 3: Load Atlas Labels NIfTI", command=self.load_atlas_nifti, style = 'Bold.TButton').grid(row=2, column=0, sticky="ew", pady=(0,6))
        ttk.Label(frm, text="Atlas Labels NIfTI:", style = 'TLabel').grid(row=2, column=1, sticky="e", pady=(0,6))
        self.atlas_nifti_lbl = ttk.Label(frm, text="(none)", style = 'Custom1.TLabel')
        self.atlas_nifti_lbl.grid(row=2, column=2, sticky="w", pady=(0,6))
        ## Generate Masks
        ttk.Button(frm, text="Step 4: Generate Masks from Atlas", command=self.generate_masks_button, style = 'Bold.TButton').grid(row=3, column=0, sticky="w", pady=(0,6))

        
        # --- Number of Groups / Conditions inputs ---
        ## Crete Name Fields
        ttk.Button(frm, text="Step 5a: Setup Design", command=self.create_group_condition_name_fields, style = 'Bold.TButton').grid(row=4, column=0, columnspan=1, sticky="ew", pady=(0,2))
        ## Groups
        ttk.Label(frm, text="Number of Groups:", style = 'TLabel').grid(row=5, column=0, sticky="e", padx=(0,2))
        self.num_groups_var = tk.IntVar(value=1)
        self.num_groups_entry = ttk.Entry(frm, textvariable=self.num_groups_var, width=6, style = 'TEntry')
        self.num_groups_entry.grid(row=5, column=1, sticky="w")
        ## Conditions
        ttk.Label(frm, text="Number of Conditions:", style = 'TLabel').grid(row=6, column=0, sticky="e", padx=(0,2))
        self.num_conditions_var = tk.IntVar(value=1)
        self.num_conditions_entry = ttk.Entry(frm, textvariable=self.num_conditions_var, width=6, style = 'TEntry')
        self.num_conditions_entry.grid(row=6, column=1, sticky="w")
        # --- Dynamic frame for group/condition name inputs and N-value grid ---
        # This is where the generated fields (Grp1, Grp2, Con1, Con2, and N-values) will appear.
        self.dynamic_frame = ttk.Frame(frm, relief="groove", borderwidth=2)
        self.dynamic_frame.grid(row=8, column=0, columnspan=5, sticky="ew", pady=(2,6))
        # Put a short instruction in the dynamic_frame initially
        ttk.Label(self.dynamic_frame, text="Specify number of groups and conditions above, then click 'Setup Design'.").grid(row=0, column=0, padx=8, pady=8, sticky="ew")


        # Statistics toggles
        l_tmp = ttk.Label(text="Step 6: Select Statistics to Compute", style = 'Bold.TLabel')
        stats_frame = ttk.LabelFrame(frm, labelwidget=l_tmp, relief="groove", borderwidth=2)
        stats_frame.grid(row=9, column=0, columnspan=5, pady=8, sticky="ew")
        self.stat_vars = [tk.BooleanVar(master=self.root, value=False) for _ in self.stat_names]
        for i, name in enumerate(self.stat_names):
            cb = ttk.Checkbutton(stats_frame, text=name, variable=self.stat_vars[i], style = 'TCheckbutton')
            cb.grid(row=i // 5, column=i % 5, sticky="w", padx=4, pady=2)

        # --- Threshold and Segment Steps
        # Threshold field
        ttk.Label(frm, text="Step 7: Threshold", style = 'Bold.TLabel').grid(row=10, column=0, sticky="w")
        # Threshold field
        ttk.Label(frm, text="Threshold (leave blank for none):").grid(row=11, column=0, sticky="e")
        self.threshold_entry = ttk.Entry(frm, width=10, style = 'TEntry')
        self.threshold_entry.grid(row=11, column=1, sticky="w")
        # Run Segmentation 
        ttk.Button(frm, text="Step 8: Run Segmentation", command=self.run_segmentation_button, style = 'Custom.TButton').grid(row=12, column=0, columnspan=5, sticky="ew", pady=(6,6))

        # Plotting controls
        # plot_frame = ttk.LabelFrame(frm, text="Plotting / Export")
        # plot_frame.grid(row=14, column=0, columnspan=5, sticky="ew", pady=8)
        # ttk.Label(plot_frame, text="Y variable:").grid(row=0, column=0, sticky="e")
        # self.y_var = tk.StringVar(value="Mean")
        # self.y_entry = ttk.Combobox(plot_frame, textvariable=self.y_var,values=["FAV", "Mean", "SegVol"], width=12).grid(row=0, column=1, sticky="w")
        # ttk.Label(plot_frame, text="Fill:").grid(row=0, column=2, sticky="e")
        # self.fill_var = tk.StringVar(value="Condition")
        # self.fill_entry = ttk.Combobox(plot_frame, textvariable=self.fill_var,values=["Condition", "Group"], width=12).grid(row=0, column=3, sticky="w")
        # ttk.Button(plot_frame, text="Generate Graphs", command=self.generate_all_column_graphs).grid(row=1, column=0, columnspan=2, pady=6)
        # ttk.Button(plot_frame, text="Generate Example Heatmap", command=self.generate_example_heatmap).grid(row=1, column=2, columnspan=2, pady=6)

        # Status and progress
        self.status_lbl = ttk.Label(frm, text="Status: Ready", anchor = "w", style = 'Custom2.TLabel')
        self.status_lbl.grid(row=13, column=0, columnspan=2, sticky="ew", pady=6)
        self.progress = ttk.Progressbar(frm, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=13, column=2, sticky="e")

        # Preview area
        # preview_frame = ttk.LabelFrame(self.root, text="Preview")
        # preview_frame.grid(row=13, column=0, sticky="nsew", padx=8, pady=8)
        # preview_frame.columnconfigure(0, weight=1)
        # preview_frame.rowconfigure(0, weight=1)
        # self.preview_fig = plt.Figure(figsize=(6, 3))
        # self.preview_ax = self.preview_fig.add_subplot(111)
        # self.canvas = FigureCanvasTkAgg(self.preview_fig, master=preview_frame)
        # self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # --------------------------
    # --- Output directories ---
    # --------------------------
    # Change the current working directory to the script's directory
    def select_save_directory(self):
        """Opens a directory selection dialog and returns the chosen path."""
        save_directory = filedialog.askdirectory(title="Select Directory to Save Output Files from Segmentation")
        if not save_directory:
            return
        try:
            os.chdir(save_directory)
            self.odir_lbl.config(text=Path(save_directory))
            self.status("Output directories generated.")
        except Exception as e:
            messagebox.showerror("Error", f"Not a directory:\n{e}")
            traceback.print_exc()
        self.directories = (
            Path(save_directory, "Masks"),
            Path(save_directory, "OutputData"),
            Path(save_directory, "OutputData/ColumnGraphs"),
            #Path(save_directory, "OutputData/Heatmaps"), # future implementations
            Path(save_directory, "OutputData/CSVs")
            )
        for d in self.directories[0:]:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)

    # ----------------------------------
    # Group and Condition Dynamic Fields
    # ----------------------------------
    def create_group_condition_name_fields(self):
        """Create dynamic Group name fields, Condition name fields, and the Group x Condition N-value grid."""
        
        # Clear previous widgets
        for w in self.dynamic_frame.winfo_children():
            w.destroy()
        
        # Read counts safely
        try:
            n_groups = int(self.num_groups_var.get())
            n_conditions = int(self.num_conditions_var.get())
            if n_groups < 1 or n_conditions < 1:
                raise ValueError("Counts must be >= 1")
        except Exception as e:
            messagebox.showerror("Invalid counts",
                                f"Please enter valid positive integers for groups and conditions.\nDetails: {e}")
            return

        # Storage
        self.group_name_vars = []
        self.cond_name_vars = []
        self.n_matrix_vars = {}  # (g_idx, c_idx) -> tk.IntVar

        # Column/row headings
        ttk.Label(self.dynamic_frame, text="Groups").grid(row=0, column=0,padx=0, pady=4, sticky="s")
        ttk.Label(self.dynamic_frame, text="Conditions").grid(row=0, column=1,padx=0, pady=4, sticky="s")
        ttk.Label(self.dynamic_frame, text="N per Group x Condition").grid(row=0, column=2, padx=0, pady=4, sticky="s")

        # Create group name entries (vertical)
        for g in range(n_groups):
            var = tk.StringVar(value=f"Grp{g+1}")
            self.group_name_vars.append(var)
            ttk.Entry(self.dynamic_frame, textvariable=var, style = 'TEntry', width=10).grid(row=1 + g*n_conditions, column=0, padx=0, pady=4, sticky="s")

            # Create condition name entries (horizontal, above N-value grid)
            for c in range(n_conditions):
                var = tk.StringVar(value=f"Con{c+1}")
                self.cond_name_vars.append(var)
                ttk.Entry(self.dynamic_frame, textvariable=var, style = 'TEntry', width=10).grid(row=1 + g*n_conditions + c, column=1, padx=0, pady=4, sticky="s")
                
                nvar = tk.IntVar(value=1)
                self.n_matrix_vars[(g, c)] = nvar
                ttk.Entry(self.dynamic_frame, textvariable=nvar, style = 'TEntry', width=6).grid(row=1 + g*n_conditions + c, column=2, padx=0, pady=4, sticky="s")


        # Save / apply button
        def _save_dynamic_settings():
            try:
                for (g, c), v in self.n_matrix_vars.items():
                    val = int(v.get())
                    if val < 0:
                        raise ValueError("N must be non-negative")
                self.status("Group/Condition names and N-values saved.")
            except Exception as e:
                messagebox.showerror("Invalid N-values",
                                    f"Please ensure all N-values are non-negative integers.\n{e}")
                return

        ttk.Button(self.dynamic_frame, text="Step 5b: Save Design Settings", command=_save_dynamic_settings, style = 'Bold.TButton') \
            .grid(row=2 + n_groups * n_conditions, column=0, columnspan=2, padx = 2, pady=(2, 4), sticky="w")


    # -----------------------------
    # File loaders & mask generation
    # -----------------------------
    def load_atlas_csv(self):
        """Load the Atlas LUT CSV into self.lut_df."""
        if self.directories is None:
            messagebox.showwarning("Select output directory first", "Please select an output directory first.")
            return
        file = filedialog.askopenfilename(title="Select atlas LUT CSV", filetypes=[("CSV", "*.csv")])
        if not file:
            return
        try:
            lut = safe_read_csv(file)
            self.lut_df = lut
            self.atlas_lbl.config(text=Path(file).name)
            self.status("Atlas LUT loaded.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load atlas LUT:\n{e}")
            traceback.print_exc()

    def load_atlas_nifti(self):
        """Load atlas label NIfTI into self.atlas_nifti (dict with data/affine/header/path)."""
        if self.directories is None:
            messagebox.showwarning("Select output directory first", "Please select an output directory first.")
            return
        file = filedialog.askopenfilename(title="Select atlas labels NIfTI", filetypes=[("All files", "*.*"),("NIfTI", "*.nii")])
        if not file:
            return
        try:
            data, aff, hdr = load_nifti_as_numpy(file)
            self.atlas_nifti = {"data": data, "affine": aff, "header": hdr, "path": file}
            self.atlas_nifti_lbl.config(text=Path(file).name)
            self.status("Atlas NIfTI loaded.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load atlas NIfTI:\n{e}")
            traceback.print_exc()

    def generate_masks_button(self):
        """
        Generate binary masks from loaded atlas and LUT.
        Must be run BEFORE 'Run Segmentation'. This function caches masks in self.masks.
        """
        if self.directories is None:
            messagebox.showwarning("Select output directory first", "Please select an output directory first.")
            return
        savemasks = False
        if getattr(self, "atlas_nifti", None) is None:
            messagebox.showwarning("Missing atlas NIfTI", "Load atlas labels NIfTI first.")
            return
        if self.lut_df is None:
            messagebox.showwarning("Missing LUT", "Load atlas LUT CSV first.")
            return
        if messagebox.askyesno("SAVE QUERY","Do you want to save masks as NIfTI files?"):
            savemasks = True
        if savemasks and (self.directories[0]) is not None and (len(os.listdir(self.directories[0])) != 0):
            if not messagebox.askyesno("Mask overwrite warning",
                                       "Do you want to overwrite existing masks?"):
                return
            self.status("Overwriting existing masks.")
        
        # Create masks only for LUT indices found in atlas
        try:
            self.masks = generate_masks(self.atlas_nifti, self.lut_df, save_dir=self.directories[0], save_masks=savemasks)
            self.status(f"Generated {len(self.masks)} masks.")
        except Exception as e:
            messagebox.showerror("Mask error", f"Failed to generate masks:\n{e}")
            traceback.print_exc()

    # -----------------------------
    # Run segmentation
    # -----------------------------
    def run_segmentation_button(self):
        """
        Build a single images DataFrame by prompting the user to select the N files for each
        Group x Condition combination and then call process_nifti_files() once to compute
        all segment statistics. The final combined DataFrame (one row per segment per image)
        is saved via a user file-save dialog.
        """
        # Validate output directory
        if self.directories is None:
            messagebox.showwarning("Select output directory first", "Please select an output directory first.")
            return
        # Validate LUT, atlas, and masks
        if self.lut_df is None:
            messagebox.showerror("Missing LUT", "Please load the Atlas LUT CSV before segmentation.")
            return
        if getattr(self, "atlas_nifti", None) is None:
            messagebox.showerror("Missing atlas NIfTI", "Please load the Atlas labels NIfTI before segmentation.")
            return
        if getattr(self, "masks", None) is None or len(self.masks) == 0:
            messagebox.showerror("Missing masks", "Please click 'Generate Masks from Atlas' before running segmentation.")
            return
        
        stat_test = [bool(v.get()) for v in self.stat_vars]
        if (np.sum(stat_test) == 0) or len(self.masks) == 0:
            messagebox.showerror("No Statistics Selected", "Please select at least one statistic.")
            return

        # Validate dynamic inputs (group/condition names and N-values)
        if not hasattr(self, "group_name_vars") or not hasattr(self, "cond_name_vars") or not hasattr(self, "n_matrix_vars"):
            messagebox.showerror("Missing group/condition info", "Please create and save Group/Condition name fields first.")
            return

        # Build group/condition lists and N-matrix
        groups = [v.get() for v in self.group_name_vars]
        conditions = [v.get() for v in self.cond_name_vars]
        n_matrix = np.zeros((len(groups), len(conditions)), dtype=int)
        for (g, c), var in self.n_matrix_vars.items():
            try:
                n_matrix[g, c] = int(var.get())
            except Exception:
                n_matrix[g, c] = 0

        total_images_expected = int(np.sum(n_matrix))
        if total_images_expected == 0:
            messagebox.showwarning("No images specified", "Sum of N-values is zero. Please set N-values for at least one Group × Condition.")
            return

        # Build the list of image rows (one per image) by prompting per Group x Condition
        images_rows = []  # list of dicts: each dict is one row for the images DataFrame used by process_nifti_files
        threshold_value = None
        thr_txt = self.threshold_entry.get().strip()
        if thr_txt == "":
            threshold_value = None
        else:
            try:
                threshold_value = float(thr_txt)
            except Exception:
                threshold_value = None

        # Ask user to select files for each combination
        for g_idx, g_name in enumerate(groups):
            for c_idx, c_name in enumerate(conditions):
                n_images = n_matrix[g_idx, c_idx]
                if n_images <= 0:
                    continue

                # Prompt explaining what to select
                messagebox.showinfo("Select files",
                                    f"Select {n_images} image(s) for Group '{g_name}', Condition '{c_name}'.\n")

                files = filedialog.askopenfilenames(
                    title=f"Select {n_images} NIfTI file(s) for {g_name} - {c_name}",
                    filetypes=[("NIfTI files", "*.nii")]
                )
                if not files or files is None:
                    return
                if len(files) != n_images:
                    messagebox.showwarning("File count mismatch", f"You selected {len(files)} files for{g_name}-{c_name}; expected {n_images}. "f"Reselect files to match expected count, or change counts and try again.")
                    return


                # Append rows (one per selected file)
                # Subject index is assigned in the order of selected files for this combination (1..len(files))
                for subj_i, fpath in enumerate(files, start=1):
                    row = {
                        "Image": str(fpath),
                        "Group": g_name,
                        "Condition": c_name,
                        "SubID": subj_i,
                        "Threshold": threshold_value
                    }
                    # Add booleans for stats (process_nifti_files uses selection flags from output_df)
                    for i, stat_name in enumerate(self.stat_names):
                        row[stat_name] = bool(self.stat_vars[i].get())
                    images_rows.append(row)

        if len(images_rows) == 0:
            messagebox.showwarning("No images", "No images collected for segmentation.")
            return

        # Build images DataFrame (this is the input to process_nifti_files())
        images_df = pd.DataFrame(images_rows)
        self.output_df = images_df.copy()  # store for record

        # Build stats_boolean from first row (consistent across all rows)
        stats_boolean = [bool(images_df.iloc[0].get(name, False)) for name in self.stat_names]
        self.stats_boolean = stats_boolean

        # Disable UI buttons during processing
        self.status("Starting segmentation...")
        self.progress["value"] = 0
        self.progress["maximum"] = len(images_df) * max(1, len(self.masks))
        self.root.update_idletasks()

        # Run segmentation in background thread to keep UI responsive
        t = threading.Thread(target=self._run_processing_thread, args=(images_df, self.masks, self.lut_df, stats_boolean), daemon=True)
        t.start()

    def _run_processing_thread(self, images_df, masks_arr, lut_df, stats_boolean):
        """
        Background thread that calls process_nifti_files(...) once for the entire images_df,
        merges lookup info (SegAbbr, SegGroup, Domain), and prompts user to save the final CSV.
        """
        try:
            # progress callback will be invoked by process_nifti_files
            def progress_cb(processed, total, message):
                # schedule update on main thread
                self.root.after(0, lambda: self._update_progress(processed, total, message))

            # Run the heavy computation (single call for all images)
            res_df = process_nifti_files(nifti_df=images_df,
                                         masks_arr=masks_arr, segment_lut=lut_df,
                                         stats_boolean=stats_boolean, progress_callback=progress_cb)

            # Attach LUT-derived columns: SegAbbr (already in 'Segment'), SegGroup, Domain
            # lut_df: Index, SegmentName, SegAbbr, SegGroup, Domain
            # process_nifti_files returned 'Segment' == SegAbbr, so merge on that value
            try:
                lut_subset = lut_df["SegAbbr", "SegGroup", "Domain"]
                res_df = res_df.merge(lut_subset, on="SegAbbr", how="left")
            except Exception:
                # if mapping fails, continue without additional columns
                pass

            # Add back per-image metadata that process_nifti_files fills from input_df rows (image name, group, condition, subid)
            # process_nifti_files sets 'Image' to filename only; ensure full path is kept for traceability by merging on Image if needed
            # We already included Group/Condition/SubID in each images_df row passed to process_nifti_files so res_df should already have them.
            # If not, we can reconstruct from images_df mapping (Image -> Group/Condition/SubID)
            # Ensure consistent column names: Image (filename), Group, Condition, SubID
            # Save final dataframe and prompt user for save
            self.summary_df = res_df

            # Ask user where to save final combined CSV (on main thread)
            def _ask_and_save():
                save_path = filedialog.asksaveasfilename(
                    initialdir=self.directories[3],
                    initialfile="segmentation_results.csv",
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")],
                    title="Save combined segmentation CSV"
                )
                if save_path:
                    try:
                        self.summary_df.to_csv(save_path, index=False)
                        messagebox.showinfo("Saved", f"Segmentation results saved to:\n{save_path}")
                        self.status(f"Segmentation complete. Saved to {Path(save_path).name}")
                    except Exception as e:
                        messagebox.showerror("Save error", f"Failed to save CSV:\n{e}")
                else:
                    self.status("Segmentation complete. Save cancelled by user.")

            self.root.after(0, _ask_and_save)

        except Exception as e:
            # Ensure exceptions are shown on main thread
            self.root.after(0, lambda: messagebox.showerror("Processing error", f"An error occurred during segmentation:\n{e}"))
            traceback.print_exc()
            self.root.after(0, lambda: self.status("Segmentation failed."))

    # -----------------------------
    # Progress & preview helpers
    # -----------------------------
    def _update_progress(self, processed, total, message):
        """Update progress bar and status label (called from background thread via after())."""
        try:
            self.status(message)
            self.progress["maximum"] = total if total > 0 else 1
            self.progress["value"] = processed
        except Exception:
            pass

    def _update_preview(self, fig):
        """Replace preview axis with a small figure (best-effort)."""
        try:
            self.preview_fig.clf()
            src_ax = fig.axes[0]
            dst_ax = self.preview_fig.add_subplot(111)
            for line in src_ax.get_lines():
                dst_ax.plot(line.get_xdata(), line.get_ydata())
            dst_ax.set_title(src_ax.get_title())
            self.canvas.draw_idle()
        except Exception:
            self.preview_ax.clear()
            self.preview_ax.text(0.5, 0.5, "Preview unavailable", ha="center")
            self.canvas.draw_idle()

    def status(self, txt):
        """Set status label text (thread-safe caller uses .after if needed)."""
        try:
            self.status_lbl.config(text=txt, style = 'Custom2.TLabel')
            self.root.update_idletasks()
        except Exception:
            pass
    
    def run(self):
        self.root.mainloop()