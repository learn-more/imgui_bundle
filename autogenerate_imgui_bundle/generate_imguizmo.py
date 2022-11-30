from typing import Optional
import copy
import os

import litgen
from codemanip import amalgamated_header


_THIS_DIR = os.path.dirname(__file__)
BUNDLE_DIR = os.path.realpath(_THIS_DIR + "/..")
CPP_GENERATED_PYBIND_DIR = BUNDLE_DIR + "/bindings"

HEADER_PARENT_DIR = BUNDLE_DIR + "/external/ImGuizmo"
STL_SUBDIR = "ImGuizmoStl"
OFFICIAL_SUBDIR = "ImGuizmo"


def make_amalgamated_header(header_file: str) -> str:
    options = amalgamated_header.AmalgamationOptions()

    options.base_dir = HEADER_PARENT_DIR
    options.local_includes_startwith = OFFICIAL_SUBDIR
    options.include_subdirs = [OFFICIAL_SUBDIR]
    options.main_header_file = STL_SUBDIR + "/" + header_file

    amalgamation = amalgamated_header.amalgamation_content(options)
    return amalgamation


def autogenerate_imguizmo():
    print("autogenerate_imguizmo")

    output_cpp_pydef_file = CPP_GENERATED_PYBIND_DIR + "/pybind_imguizmo.cpp"
    output_stub_pyi_file = CPP_GENERATED_PYBIND_DIR + "/imgui_bundle/imguizmo.pyi"

    # Configure options
    options = litgen.LitgenOptions()
    options.class_override_virtual_methods_in_python__regex = r".*"
    options.struct_create_default_named_ctor__regex = ""
    options.python_run_black_formatter = False

    generator = litgen.LitgenGenerator(options)

    def process_one_file_backup_options(code: Optional[str], filename: str, options: litgen.LitgenOptions):
        options_backup = generator.lg_context.options
        generator.lg_context.options = options
        generator.process_cpp_code(code=code, filename=filename)
        generator.lg_context.options = options_backup

    def process_one_amalgamated_file(header_file: str, options: litgen.LitgenOptions):
        amalgamation = make_amalgamated_header(header_file)
        process_one_file_backup_options(code=amalgamation, filename=header_file, options=options)

    # Process ImCurveEditStl
    options_curve = copy.deepcopy(options)
    options_curve.fn_exclude_by_name__regex = "^Edit$|^GetPointCount$|^GetPoints$"
    process_one_amalgamated_file("ImCurveEditStl.h", options_curve)

    # Process ImGradientStl
    options_gradient = copy.deepcopy(options)
    options_gradient.fn_exclude_by_name__regex = "^Edit$|^GetPointCount$|^GetPoints$"
    process_one_amalgamated_file("ImGradientStl.h", options_gradient)

    # Process ImZoomSlider
    options_slider = copy.deepcopy(options)
    options_slider.srcmlcpp_options.ignored_warning_parts = ["Ignoring template function"]
    options_slider.var_names_replacements.add_last_replacement("im_gui_zoom_slider_flags_", "")
    options_slider.type_replacements.add_last_replacement("ImGuiPopupFlags_", "ImGuiZoomSliderFlags_")
    process_one_amalgamated_file("ImZoomSliderStl.h", options_slider)

    # Process ImSequencer:
    # abandoned due to double pointer in the public API
    # --------------
    # options_sequencer = copy.deepcopy(options)
    # options_sequencer.fn_exclude_by_name__regex = r"^Get$"
    # process_one_amalgamated_file("ImSequencerStl.h", options_sequencer)

    # Process GraphEditor:
    # cowardly avoided because of double pointers in structs + pointer to enum in params
    # --------------
    # options_graph = copy.deepcopy(options)
    # header_file = f"{HEADER_PARENT_DIR}/{OFFICIAL_SUBDIR}/GraphEditor.h"
    # process_one_file_backup_options(code=None, filename=header_file, options=options_graph)


    generator.write_generated_code(
        output_cpp_pydef_file=output_cpp_pydef_file,
        output_stub_pyi_file=output_stub_pyi_file,
    )


if __name__ == "__main__":
    autogenerate_imguizmo()
