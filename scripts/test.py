from argparse import ArgumentParser
from pathlib import Path
from fbx import FbxManager, FbxIOSettings, FbxExporter, FbxScene, IOSROOT
import traceback
import sys

try:
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-o", "--output-name", type=str, required=True, help="Name of the output FBX file")
    arg_parser.add_argument("--ascii", action="store_true", help="Export in ASCII format")
    arg_parser.add_argument("--encrypt", action="store_true", help="Export in encrypted format")
    args = arg_parser.parse_args()

    # Initialize and configure the FBX SDK manager
    fbx_manager = FbxManager()
    ios_settings = FbxIOSettings.Create(fbx_manager, IOSROOT)
    fbx_manager.SetIOSettings(ios_settings)

    # Configure the output path
    output_path = Path(args.output_name)
    if output_path.suffix.lower() != ".fbx":
        output_path = output_path.with_suffix(".fbx")

    # Initialize the FBX exporter
    fbx_exporter = FbxExporter.Create(fbx_manager, "")
    file_format = -1
    if args.ascii:
        file_format = fbx_manager.GetIOPluginRegistry().FindWriterIDByDescription("FBX ascii (*.fbx)")
    if args.encrypt:
        file_format = fbx_manager.GetIOPluginRegistry().FindWriterIDByDescription("FBX encrypted (*.fbx)")

    if not fbx_exporter.Initialize(str(output_path), file_format, fbx_manager.GetIOSettings()):
        print(f"Error initializing FBX exporter: {fbx_exporter.GetStatus().GetErrorString()}")
        exit(1)

    # Create a new FBX scene
    new_scene = FbxScene.Create(fbx_manager, "New Scene")

    # Export the scene
    if not fbx_exporter.Export(new_scene):
        print(f"Error exporting FBX scene: {fbx_exporter.GetStatus().GetErrorString()}")
        exit(1)

    print(f"Successfully exported FBX file to: {output_path}")

    # Cleanup
    fbx_manager.Destroy()
except BaseException:
    traceback.print_exc()
    raise
finally:
    print("finally block reached")
    sys.exit(0)
