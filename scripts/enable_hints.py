with open("cache/fbxbind/pyproject.toml", "r") as f:
    content = f.read()

# Locate the existing block and inject the flag right underneath it
target = "[tool.sip.bindings.fbx_module]"
patched = f"{target}\npep484-pyi = true"

if target in content and "pep484-pyi" not in content:
    content = content.replace(target, patched)
    with open("cache/fbxbind/pyproject.toml", "w") as f:
        f.write(content)
    print("Successfully injected type-stub flag into the existing block!")
else:
    print("Flag already present or target block not found.")
