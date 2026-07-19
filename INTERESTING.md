## A Thing I Noticed About the Official Pre-compiled Python 3.10 FBX SDK

When testing Linux packages after building them with cibuildwheel, it threw an ImportError, e.g. /tmp/tmp.wHRD5oKgiG/venv/lib/python3.11/site-packages/fbx.cpython-311-x86_64-linux-gnu.so: undefined symbol: fcntl64. The build environment was manylinux2014 with glibc 2.17, whereas fcnt164 exists in glibc 2.28 and higher. This would require the environment to be updated to manylinux_2_28.

Out of curiosity, I decided to test the official pre-compiled Python 3.10 FBX SDK wheel in a Docker container with quay.io/pypa/manylinux2014_x86_64 linux image:

```bash
docker run --rm -v "$(pwd)":/project -w /project quay.io/pypa/manylinux2014_x86_64 /bin/bash -c "/opt/python/cp310-cp310/bin/python -m pip install fbx-2020.3.9-cp310-cp310-manylinux1_x86_64.whl && /opt/python/cp310-cp310/bin/python -c 'import fbx; import os; print(os.path.dirname(fbx.__file__))' && /opt/python/cp310-cp310/bin/python scripts/test.py -o test_output"
```

Producing ImportError: /lib64/libm.so.6: version `GLIBC_2.27' not found (required by /opt/python/cp310-cp310/lib/python3.10/site-packages/fbx.cpython-310-x86_64-linux-gnu.so). This may indicate that the compatibility tag on the official package (manylinux1) is misleading. In the following section, I have run the same test on manylinux_2_28 this time:

```bash
docker run --rm -v "$(pwd)":/project -w /project quay.io/pypa/manylinux_2_28_x86_64 /bin/bash -c "/opt/python/cp310-cp310/bin/python -m pip install fbx-2020.3.9-cp310-cp310-manylinux1_x86_64.whl && /opt/python/cp310-cp310/bin/python -c 'import fbx; import os; print(os.path.dirname(fbx.__file__))' && /opt/python/cp310-cp310/bin/python scripts/test.py -o test_output"
```

Producing:

```bash
Successfully exported FBX file to: test_output.fbx
finally block reached
```
