# Shared Object Symbol Resolution

This plugin resolves symbols in shared objects (.so, currently only elf files are supported). The plugin will open any shared object files if needed.

# Usage

The plugin registers one command - "Resolve Shared Library Import". Right click on an external symbol (i.e. `004040d8  extern puts`), and select 'Resolve Shared Library Import'. This currently only works on ELF files.

TODO: Screenshots.

# Installation

Clone or symlink this repository into your plugin folder. (https://docs.binary.ninja/guide/plugins.html#using-plugins)

Ensure that your system has `ldd` installed.
