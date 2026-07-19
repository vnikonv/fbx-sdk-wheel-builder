## What is this repository for?
A GitHubActions-based automated workflow for building FBX Python SDK .whl packages from FBX SDK and FBX Python Bindings.

By popular demand, FBX Python SDK packages are built for Python versions 3.7, 3.9. 3.11, 3.13, and FBX SDK version 2020.3.9
with hints stub files (.pyi) enabled. Each version is compiled for Windows (win_AMD64; with VS_2022), Linux (manylinux2014_x86_64),
and macOS (macosx_10_15_x86_64, macosx_11_0_ARM64, macosx_10_15_universal2).

Since Python 3.7 is not officially supported on Apple Silicon ARM (and cannot be compiled from 3.7.17 tarball without Rosetta), macosx_11_0_ARM64 and macosx_10_15_universal2 packages for this version will not be built. In addition, manylinux2014 image is used due to manylinux1's conflicts with Python versions 3.11 and 3.13 as well as general deprecation.

Currently, the package for Python 3.7 on macOS is compiled using MACOSX_DEPLOYMENT_TARGET = "11.7" despite being labeled 10.15, because the Python 3.7 interpreter itself was configured for an 11.7 minimum. This will be resolved in the future with the introduction of cibuildwheel building and testing workflows in build-windows.yml and build-macos.yml, allowing for automated compilation across native runner environments using the earliest compatible deployment targets.

## Acknowledgements
I would like to specifically thank the author of [this article](https://zenn.dev/nadegata_memo/articles/47690559881ee5#4.1.-fbx-sdk-%E3%81%AE%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB) explaining and providing clear instructions on building an FBX Python SDK package. The code for test.py is copied directly from the article, with a few modifications.

## Legal Disclaimer
This project does not redistribute the Autodesk FBX SDK or its Python bindings nor does it publish the resulting wheels. No Autodesk code is committed into the repository.

During the build process, the required SDK and bindings are downloaded directly from Autodesk's official sources. Users are responsible for complying with Autodesk's licence terms when using the SDK.

Use the Python packages produced by this workflow at your own risk. Tests targeting Python version 3.13 have repeatedly failed with segmentation faults across operating systems, possibly hinting at compatibility issues with either C API, ABI, and/or bindings.
