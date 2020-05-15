from binaryninja.plugin import PluginCommand
from binaryninja.mainthread import execute_on_main_thread_and_wait
from binaryninja import BinaryViewType, SymbolType, interaction
from binaryninjaui import UIContext, DockHandler
import binaryninjaui
import subprocess
import os

# TODO: Custom list of libraries to look through


def display_block(bv, addr):
    view = bv.view

    # Navigate to location in view
    result = bv.file.navigate(view, addr)
    if result is False:
        view = "Linear:" + view.split(":")[1]
        result = bv.file.navigate(view, addr)

    # Switch displayed view
    UIContext.activeContext().navigateForBinaryView(bv, addr)


def get_all_binaryviews():
    all_binaryviews = []
    dock = DockHandler.getActiveDockHandler()
    if not dock:
        log_error("No dock handler. This should not happen.")
        return
    viewFrame = dock.getViewFrame()
    if not viewFrame:
        log_error("No open binary")
        return
    stackedViewFrames = viewFrame.parent()  # QStackedWidget
    for i in range(stackedViewFrames.count()):
        viewFrame = stackedViewFrames.widget(i)
        if isinstance(viewFrame, binaryninjaui.ViewFrame):
            # New tab is not a ViewFrame
            viewInterface = viewFrame.getCurrentViewInterface()
            binaryview = viewInterface.getData()
            all_binaryviews.append(binaryview)

    return all_binaryviews


def open_file_tab(filename: str):
    # TODO: Save libc analysis? (Renaming symbols might cause some issues...)
    execute_on_main_thread_and_wait(
        lambda: UIContext.allContexts()[0].openFilename(filename)
    )


def get_linked_libraries(bv):
    stdout = subprocess.check_output("ldd {}".format(bv.file.filename), shell=True)
    a = stdout.split(b" ")
    libraries = []
    for line in a:
        if line.startswith(b"/"):
            libraries.append(os.path.realpath(str(line, "utf8")))

    return libraries


def resolve_imports(bv, address):
    library_bvs = []
    libraries = get_linked_libraries(bv)

    needed_libraries = libraries.copy()

    all_bvs = get_all_binaryviews()

    for potential_bv in all_bvs:
        if potential_bv.file.filename in libraries:
            try:
                needed_libraries.remove(potential_bv.file.filename)
            except ValueError:
                pass

    for library in needed_libraries:
        open_file_tab(library)
        # TODO: Wait for symbols to be resolved, or does this already happen

    all_bvs = get_all_binaryviews()
    for potential_bv in all_bvs:
        if potential_bv.file.filename in libraries:
            library_bvs.append(potential_bv)

    # TODO: Get currently selected symbol instead of checking the address
    symbols = bv.get_symbols_of_type(SymbolType.ExternalSymbol)
    external_symbol = False
    for symbol in symbols:
        if symbol.address == address:
            for library_bv in library_bvs:
                for library_symbol in library_bv.get_symbols_by_name(symbol.name):
                    if (
                        library_symbol.auto
                    ):  # Ensure that renamed symbols are not counted
                        display_block(library_bv, library_symbol.address)
                        return
            interaction.show_message_box(
                "Shared Object Symbol Resolution",
                "Selected symbol not found in shared libraries: {}".format(library_bvs),
            )
            return

    interaction.show_message_box(
        "Shared Object Symbol Resolution", "Address not an external symbol."
    )


def is_valid(bv, address):
    return bv.view_type == "ELF"


def register_commands():
    """
    Register commands
    """

    PluginCommand.register_for_address(
        "Resolve Shared Library Import",
        "Resolves an import from a shared library, and jumps to its definition.",
        action=resolve_imports,
        is_valid=is_valid,
    )


register_commands()
