#!/usr/bin/env python
import zipfile
import os
import asyncio
from typing import List
import sys
from concurrent.futures import ProcessPoolExecutor
import argparse

# Define the file path (current directory) and the zip path (zips directory)
origin_path = os.getcwd() + "/"
zip_folder_path = origin_path + "zips/"

# files of folders to exclude from compression
not_compress_this = ["omega_compresser.py", "zips"]

# words contained in the file name to replace with
replacers = {
    ".txt": "",
    "./": "",
}


async def init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega_compresser",
        description="Compress quickly all files in a directory",
        usage="""
        Example:
        python omega_compresser.py . | compress all files in the current directory into zips directory
        python omega_compresser.py -r D:Z,.txt:,A:R . | compress all files in the current directory, and replace the .txt with an empty string and the A with R in all the files name
        python omega_compresser.py -n *.txt:*.zip . | compress all files in the current directory except the ones with .txt or .zip extension
        python omega_compresser.py -p /path/to/files -o /path/to/zips | compress all files in the specified directory into the specified zips directory
        """,
    )

    parser.add_argument(
        "--replacers",
        "-r",
        help="""Replacers to replace in the file name, how it works RBCD.txt -> RABCZ.zip,
        how to use --replacers D:Z,.txt:,A:R. Add the replacers separaded by comma,
        trailing coma is not required. If you want to use an empty value
        just let the colon alone. It's not necessary include the .zip replacer,
        it will be added automatically""",
        type=str,
    )
    parser.add_argument(
        "--exclude",
        "-e",
        help="Exclude files in the compression, how to use it --exclude *.txt:*.zip",
        type=str,
    )
    parser.add_argument(
        "--input_path",
        "-p",
        help="Path to compress, how to use it --input_path /path/to/files",
        type=str,
    )
    parser.add_argument(
        "--output_path",
        "-o",
        help="Path to compress, how to use it --output_path /path/to/zips",
        type=str,
    )

    result = await is_printing_help(parser)
    if result:
        sys.argv.append("--help")
        print(parser.parse_args().verbose)
    return parser


async def validate_args(args: argparse.Namespace) -> None:
    if args.replacers:
        replacers_list = args.replacers.split(",")
        replacers_list = [
            kv.split(":") if len(kv.split(":")) == 2 else [kv.replace(":", ""), ""]
            for kv in replacers_list
        ]
        replacers_list = {kv[0]: kv[1] for kv in replacers_list}
        replacers.update(replacers_list)
    if args.exclude:
        not_compress_this.extend(args.exclude.split(":"))
    if args.input_path:
        global origin_path
        origin_path = args.input_path
    if args.output_path:
        global zip_folder_path
        zip_folder_path = args.output_path
        not_compress_this.append(zip_folder_path)


async def is_printing_help(parser: argparse.ArgumentParser) -> bool:
    if "--input_path" in sys.argv or "-p" in sys.argv:
        return False
    return True


async def is_win() -> bool:
    return "win" in sys.platform.lower()


def get_final_file_name_sync(file_path: str) -> str:
    """Synchronous function to generate the final file name."""
    is_windows = "win" in sys.platform.lower()
    result = file_path.split("\\")[-1] if is_windows else file_path.split("/")[-1]
    for k, v in replacers.items():
        result = result.replace(k, v)
    return result + ".zip"


def compress_file_sync(origin_file_path: str, zip_folder_path: str):
    """Synchronous function to compress a file."""
    zip_name = get_final_file_name_sync(origin_file_path)
    zipped_file_path = os.path.join(zip_folder_path, zip_name)
    print("Compressing from", origin_file_path, "to", zipped_file_path)

    try:
        with zipfile.ZipFile(
            file=zipped_file_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=zipfile.ZIP_DEFLATED,
        ) as zip_file:
            zip_file.write(origin_file_path, os.path.basename(origin_file_path))
    except Exception as e:
        print(f"Error compressing {origin_file_path}: {e}")


async def get_files_name(path: str) -> List[str]:
    # Get the files name from the path
    return [f for f in os.listdir(path) if f not in not_compress_this]


async def compress_all(original_path: str, zip_folder_path: str) -> None:
    # Create the zips directory if it doesn't exist
    os.makedirs(zip_folder_path, exist_ok=True)

    # Get the files name
    files = await get_files_name(original_path)

    # For each filem create an async compression task and add it to the tasks list
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        # Create the tasks
        tasks = []
        for file in files:
            tasks.append(
                loop.run_in_executor(
                    executor,
                    compress_file_sync,
                    os.path.join(original_path, file),
                    zip_folder_path,
                )
            )

    # await
    asyncio.gather(*tasks)

    print("All files have been compressed")


async def main() -> None:
    if not "." in sys.argv:
        args = await init_parser()
        await validate_args(args.parse_args())

    # Run the compress_all function with asyncio
    await compress_all(origin_path, zip_folder_path)


if __name__ == "__main__":
    asyncio.run(main())
