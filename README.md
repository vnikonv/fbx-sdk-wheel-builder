## What is this repository for?
A GitHubActions-based automated workflow for building FBX Python SDK .whl packages from FBX SDK and FBX Python Bindings.
It utilizes cibuildwheel and auditwheel in building and testing the produced wheels.

By popular demand, FBX Python SDK packages are built for Python versions 3.7, 3.9. 3.11, 3.13, and FBX SDK version 2020.3.9
with hints stub files (.pyi) enabled. Each version is compiled for Windows (win_AMD64; with vs2022), Linux (manylinux_2_28_x86_64),
and macOS (macosx_10_9_x86_64, macosx_11_0_ARM64, macosx_10_9_universal2).

Since Python 3.7 is not officially supported on Apple Silicon ARM (and cannot be compiled from 3.7.17 tarball without Rosetta), macosx_11_0_ARM64 and macosx_10_9_universal2 packages for this version will not be built. In addition, manylinux_2_28 image is used due to manylinux1's conflicts with Python versions 3.11 and 3.13 as well as general deprecation, and manylinux2014's [insufficient glibc version](INTERESTING.md).

## Acknowledgements
I would like to specifically thank the author of [this article](https://zenn.dev/nadegata_memo/articles/47690559881ee5#4.1.-fbx-sdk-%E3%81%AE%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB) explaining and providing clear instructions on building an FBX Python SDK package. The code for test.py is copied directly from the article, with a few modifications.

## Legal Disclaimer
This project does not redistribute the Autodesk FBX SDK or its Python bindings nor does it publish the resulting wheels. No Autodesk code is committed into the repository.

During the build process, the required SDK and bindings are downloaded directly from Autodesk's official sources. Users are responsible for complying with Autodesk's licence terms when using the SDK.

Use the Python packages produced by this workflow at your own risk. Tests targeting Python version 3.13 have repeatedly failed with segmentation faults across operating systems, possibly hinting at compatibility issues with either C API, ABI, and/or bindings/sip files. It is a known issue mentioned in the official FBX SDK Python Bindings pyproject.toml that sip versions 6.7.0 and higher (with the support for newer C API in Python 3.13) are broken for handling template FbxArray, and upon trying to force 6.7.0 anyway with --no-build-isolation, the build fails due to errors in sip files.

Python 3.13 wheels are excluded from testing, but if they were tested, segfaults would inevitably appear, preventing workflows from caching 3.13 wheels. Although, when these same wheels are used on a local computer under Windows 11, WSL, and VirtualBox Linux VMs (Rocky 8, Debian), the segfaults happen but do not interfere with the output of sample test scripts, e.g. ExportScene03. The resulting .fbx files can be successfully imported into 3D software, such as Blender, as I have tested on my personal machine. Again, I cannot guarantee it will work on yours.
