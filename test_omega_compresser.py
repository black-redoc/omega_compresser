import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import zipfile
import asyncio
import omega_compresser as oc  # Assuming the script is named omega_compresser.py


@pytest.mark.asyncio
async def test_get_files_name():
    mock_files = ["file1.txt", "file2.doc", "omega_compresser.py", "zips"]
    with patch("os.listdir", return_value=mock_files):
        files = await oc.get_files_name("/mock/path")
        assert files == ["file1.txt", "file2.doc"]


@pytest.mark.asyncio
async def test_is_win():
    with patch("sys.platform", "win32"):
        assert await oc.is_win() is True

    with patch("sys.platform", "linux"):
        assert await oc.is_win() is False


def test_get_final_file_name_sync():
    file_path = "/mock/path/file1.txt"
    expected_name = "file1.zip"
    actual_name = oc.get_final_file_name_sync(file_path)
    assert actual_name == expected_name


def test_compress_file_sync():
    origin_file = "/mock/path/file1.txt"
    zip_folder = "/mock/zips"
    expected_zip_path = os.path.join(zip_folder, "file1.zip")

    with patch("zipfile.ZipFile") as mock_zip:
        oc.compress_file_sync(origin_file, zip_folder)
        mock_zip.assert_called_once_with(
            file=expected_zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=zipfile.ZIP_DEFLATED,
        )
        mock_zip.return_value.__enter__.return_value.write.assert_called_once_with(
            origin_file, os.path.basename(origin_file)
        )


@pytest.mark.asyncio
async def test_compress_all(capsys):
    mock_files = ["file1.txt", "file2.doc"]
    original_path = "/mock/path"
    zip_folder_path = "/mock/zips"

    with patch("os.makedirs") as mock_makedirs, patch(
        "os.listdir", return_value=mock_files
    ), patch("asyncio.get_event_loop"), patch(
        "omega_compresser.compress_file_sync"
    ) as mock_compress, patch(
        "asyncio.gather"
    ):
        await oc.compress_all(original_path, zip_folder_path)

        mock_makedirs.assert_called_once_with(zip_folder_path, exist_ok=True)
        captured = capsys.readouterr()
        assert captured.out == "All files have been compressed\n"
        # assert mock_compress.call_count == len(mock_files)


@pytest.mark.asyncio
async def test_validate_args():
    args = MagicMock()
    args.replacers = "A:B,.txt:"
    args.exclude = "*.py:*.log"
    args.input_path = "/new/input"
    args.output_path = "/new/output"

    await oc.validate_args(args)

    assert oc.replacers["A"] == "B"
    assert oc.replacers[".txt"] == ""
    assert "*.py" in oc.not_compress_this
    assert "*.log" in oc.not_compress_this
    assert oc.origin_path == "/new/input"
    assert oc.zip_folder_path == "/new/output"


@pytest.mark.asyncio
async def test_main_no_args():
    with patch("sys.argv", ["omega_compresser.py"]), patch(
        "omega_compresser.init_parser"
    ) as mock_parser, patch("omega_compresser.compress_all") as mock_compress:
        mock_args = MagicMock()
        mock_args.parse_args.return_value = MagicMock()
        mock_parser.return_value = mock_args

        await oc.main()
        mock_parser.assert_called_once()
        mock_compress.assert_called_once_with(oc.origin_path, oc.zip_folder_path)
