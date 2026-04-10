# InVivoSegment.py
"""
Overview: Main function of the InVivo Atlas Segmentation package.

This script supports starting the GUI or printing usage/version info. 

Version: 1.0.0
Author: Taylor W. Uselman
Date 2025-04-09

Disclosure: Generative-AI tools (Anthropic Claude, Google Gemini and GitHub Copilot) were used for aspects of code-generation, translating between R and Python languages, debugging, and optimization as instructed by Uselman. All debugging, validations and testing were performed by Uselman. 
"""

import argparse # for command-line argument parsing
import textwrap # for formatting
import sys # system access

version = "1.0.0" # package version

def get_arg_parser(): # argument parser function
    epilog = textwrap.dedent( 
        """
        Examples:
          Start the GUI (default):
            python InVivoSegment

          Print extended usage information:
            python InVivoSegment --info

          Print version:
            python InVivoSegment --version
        """
    )
    parser = argparse.ArgumentParser(
        prog="InVivoSegment",
        description="InVivo Atlas Segmentation - start GUI or show usage information",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["gui", "info", "version"],
        default="gui",
        help="To run GUI {'gui'}, for more information {'info'}, or for version number {'version'}.",
    )
    return parser


def print_extended_info(): # print InVivoSegment information
    info = textwrap.dedent(
        """
        InVivoSegment
        -------------
        This package provides a GUI for performing segmentation of MRI images based on the InVivo Mouse Brain Atlas.

        Running modes:
          gui     Start the Tkinter-based GUI (default). This requires a
                  working display environment and the GUI dependencies.

          info    Print this extended help text and exit (no GUI imports).

          version Print package version and exit..

        Notes:
        - Importing this module will not start the GUI. Use the --mode option or run without arguments to launch the GUI.
        """
    )
    print(info)

def main(): # Main function to start GUI
    """Start the GUI. GUI imports are done here to avoid side-effects on import."""
    # Lazy imports to avoid importing heavy GUI/third-party packages at module import time
    import tkinter as tk

    # Try multiple strategies to import the GUI class. It's common for users to run the top-level script from the package folder which makes Python treat the folder as a plain directory rather than an installed package (leading to "X is not a package" ModuleNotFoundError). We attempt:
    #  1) package export: `from InVivoSegment import SegmentationApp`
    #  2) direct submodule import: `from InVivoSegment.invivo_segment_gui import SegmentationApp`
    #  3) load the module file directly via importlib if the above fail.
    SegmentationApp = None
    try:
        # Prefer package-level export if available
        from scripts import SegmentationApp as SegmentationApp  # type: ignore
    except Exception:
        try:
            from scripts.invivo_segment_gui import SegmentationApp as SegmentationApp  # type: ignore
        except Exception:
            # Last resort: load the GUI module directly from the package folder using importlib
            try:
                import importlib.util
                from pathlib import Path

                # locate the invivo_segment_gui.py file relative to this script
                this_file = Path(__file__).resolve()
                pkg_dir = this_file.parent
                gui_path = pkg_dir / "invivo_segment_gui.py"
                if gui_path.exists():
                    spec = importlib.util.spec_from_file_location("invmodule_gui", str(gui_path))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    SegmentationApp = getattr(mod, "SegmentationApp", None)
            except Exception:
                SegmentationApp = None

    if SegmentationApp is None:
        raise ImportError("Could not import SegmentationApp from InVivoSegment package or invivo_segment_gui.py")

    root = tk.Tk()
    app = SegmentationApp(root)
    app.run()

if __name__ == "__main__": # entry point for command-line execution
    parser = get_arg_parser()
    args = parser.parse_args()
    if args.mode == "info":
        print_extended_info()
        sys.exit(0)
    if args.mode == "version":
        # If you maintain a version variable, replace the string below accordingly.
        print("InVivoSegment version: " + version)
        sys.exit(0)
    if args.mode == "gui":
        main()
    else:
        print(f"ERROR: --mode argument {args.mode}, not recognized")
        sys.exit(2)
