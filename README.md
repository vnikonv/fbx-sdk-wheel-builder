### What is this repository for?
A GitHubActions-based automated workflow for building FBX Python SDK .whl packages from FBX SDK and FBX Python Bindings.

By popular demand, FBX Python SDK packages are built for Python versions 3.7, 3.9. 3.11, 3.13, and FBX SDK version 2020.3.9
with hints stub files enabled.

Each version is compiled for Windows (win_AMD64; with VS_2022), Linux (manylinux2014_x86_64),
and macOS (macosx_10_15_x86_64, macosx_11_0_ARM64, macosx_10_15_universal2).
