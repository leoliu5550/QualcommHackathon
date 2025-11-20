"""
ONNX Model Downloader - Download pre-exported INT8 ONNX models from GitHub Releases.

This script downloads pre-quantized INT8 ONNX models from GitHub Releases,
verifies checksums, and extracts them to the correct location for runtime use.
"""

import argparse
import hashlib
import sys
import tarfile
from pathlib import Path

try:
    import httpx
    from tqdm import tqdm
except ImportError:
    print("ERROR: Required dependencies not found.")
    print("Please install with: uv pip install httpx tqdm")
    sys.exit(1)


class ONNXModelDownloader:
    """Download and verify ONNX models from GitHub Releases."""

    # GitHub repository information
    GITHUB_OWNER = "yourorg"  # TODO: Update with actual GitHub org/user
    GITHUB_REPO = "QualcommHackathon"  # TODO: Update with actual repo name

    # Default model information
    DEFAULT_MODEL = "Llama-3.2-3B-Instruct"
    DEFAULT_TAG = "model-v1.0.0"  # TODO: Update with actual release tag

    # Model output directory
    MODELS_DIR = Path(__file__).parent.parent / "fileorg" / "llm_classifier" / "models"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        release_tag: str = DEFAULT_TAG,
        output_dir: Path = None,
        skip_checksum: bool = False,
    ):
        """
        Initialize downloader.

        Args:
            model_name: Model name (e.g., "Llama-3.2-3B-Instruct")
            release_tag: GitHub release tag (e.g., "model-v1.0.0")
            output_dir: Output directory (default: fileorg/llm_classifier/models)
            skip_checksum: Skip checksum verification (not recommended)
        """
        self.model_name = model_name
        self.release_tag = release_tag
        self.output_dir = output_dir or self.MODELS_DIR
        self.skip_checksum = skip_checksum

        # Construct download URLs
        self.base_url = f"https://github.com/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/releases/download/{self.release_tag}"

        # File names
        self.archive_name = f"{model_name.lower()}-int8.tar.gz"
        self.checksum_name = f"{model_name.lower()}-int8.sha256"

        # Full URLs
        self.archive_url = f"{self.base_url}/{self.archive_name}"
        self.checksum_url = f"{self.base_url}/{self.checksum_name}"

        # Local paths
        self.download_dir = Path.cwd() / "downloads"
        self.archive_path = self.download_dir / self.archive_name
        self.checksum_path = self.download_dir / self.checksum_name

    def create_download_dir(self):
        """Create download directory if it doesn't exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Download directory: {self.download_dir}")

    def download_file(self, url: str, output_path: Path, description: str = "Downloading") -> bool:
        """
        Download a file with progress bar and resume support.

        Args:
            url: URL to download from
            output_path: Path to save file
            description: Description for progress bar

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists (resume support)
            resume_pos = 0
            mode = "wb"
            if output_path.exists():
                resume_pos = output_path.stat().st_size
                mode = "ab"
                print(f"📥 Resuming download from {resume_pos} bytes")

            # Prepare headers for resume
            headers = {}
            if resume_pos > 0:
                headers["Range"] = f"bytes={resume_pos}-"

            # Stream download with progress bar
            with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=30.0) as response:
                if response.status_code == 404:
                    print(f"❌ ERROR: File not found at {url}")
                    print("   This may mean:")
                    print(f"   1. The release tag '{self.release_tag}' doesn't exist")
                    print(f"   2. The model '{self.model_name}' hasn't been uploaded yet")
                    print("   3. The file name is different than expected")
                    return False

                if response.status_code not in [200, 206]:  # 206 = Partial Content (resume)
                    print(f"❌ ERROR: HTTP {response.status_code} when downloading {url}")
                    return False

                # Get total size
                total_size = int(response.headers.get("content-length", 0))
                if response.status_code == 206:
                    # Partial content - add resume position
                    total_size += resume_pos

                # Progress bar
                with tqdm(
                    total=total_size,
                    initial=resume_pos,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=description,
                ) as pbar:
                    with open(output_path, mode) as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))

            print(f"✅ Downloaded: {output_path}")
            return True

        except httpx.TimeoutException:
            print("❌ ERROR: Download timeout. Please check your internet connection and try again.")
            return False
        except httpx.ConnectError:
            print("❌ ERROR: Cannot connect to GitHub. Please check your internet connection.")
            return False
        except Exception as e:
            print(f"❌ ERROR: Download failed: {e}")
            return False

    def check_if_split(self) -> tuple[bool, list]:
        """
        Check if the release uses split files.

        Returns:
            Tuple of (is_split: bool, part_files: list)
        """
        # Try to check if .partaa exists
        part_aa_url = f"{self.archive_url}.partaa"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.head(part_aa_url, follow_redirects=True)
                if response.status_code == 200:
                    print("📦 Detected split archive (file >2GB)")
                    # Determine number of parts by trying sequential names
                    parts = []
                    suffixes = [chr(ord("a") + i) + chr(ord("a") + j) for i in range(26) for j in range(26)]  # aa, ab, ac, ..., zz

                    for suffix in suffixes:
                        part_url = f"{self.archive_url}.part{suffix}"
                        part_file = self.download_dir / f"{self.archive_name}.part{suffix}"

                        try:
                            check_response = client.head(part_url, follow_redirects=True)
                            if check_response.status_code == 200:
                                parts.append((part_url, part_file))
                            else:
                                break  # No more parts
                        except Exception:
                            break

                    print(f"   Found {len(parts)} parts")
                    return True, parts
        except Exception:  # nosec B110: Intentionally ignore errors when checking for split files
            pass

        return False, []

    def merge_split_files(self, part_files: list) -> bool:
        """
        Merge split archive parts into single file.

        Args:
            part_files: List of part file paths

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🔗 Merging {len(part_files)} parts into {self.archive_path}...")

            with open(self.archive_path, "wb") as outfile:
                for part_file in part_files:
                    with open(part_file, "rb") as infile:
                        # Copy in chunks
                        while True:
                            chunk = infile.read(8192)
                            if not chunk:
                                break
                            outfile.write(chunk)

            print(f"✅ Merge complete: {self.archive_path}")

            # Clean up part files
            for part_file in part_files:
                part_file.unlink()
                print(f"🗑️  Cleaned up: {part_file.name}")

            return True

        except Exception as e:
            print(f"❌ ERROR: Merge failed: {e}")
            return False

    def verify_checksum(self, is_split: bool = False) -> bool:
        """
        Verify SHA256 checksum of downloaded archive.

        Args:
            is_split: Whether this was a split archive

        Returns:
            True if checksum matches, False otherwise
        """
        if self.skip_checksum:
            print("⚠️  Skipping checksum verification (not recommended)")
            return True

        try:
            # Read checksum file
            with open(self.checksum_path, "r") as f:
                checksum_lines = f.read().strip().split("\n")

            if is_split:
                # For split files, checksum file contains checksums for merged file
                # (the original archive before splitting)
                print("🔍 Verifying checksum of merged file...")
                # Use first line which should be the original archive
                expected_checksum = checksum_lines[0].split()[0]
            else:
                # Single file
                expected_checksum = checksum_lines[0].split()[0]

            print(f"   Expected: {expected_checksum}")

            # Calculate actual checksum
            sha256 = hashlib.sha256()
            with open(self.archive_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            actual_checksum = sha256.hexdigest()
            print(f"   Actual:   {actual_checksum}")

            if actual_checksum == expected_checksum:
                print("✅ Checksum verified successfully")
                return True
            else:
                print("❌ ERROR: Checksum mismatch!")
                print("   This may indicate:")
                print("   1. Downloaded file is corrupted")
                print("   2. Download was interrupted")
                print("   3. Security issue (file tampered)")
                print("\n   Recommended action:")
                print(f"   - Delete {self.archive_path}")
                print("   - Re-run this script to download again")
                return False

        except Exception as e:
            print(f"❌ ERROR: Checksum verification failed: {e}")
            return False

    def extract_archive(self) -> bool:
        """
        Extract downloaded archive to models directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            print("📦 Extracting archive...")
            print(f"   From: {self.archive_path}")
            print(f"   To:   {self.output_dir}")

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Extract with progress
            with tarfile.open(self.archive_path, "r:gz") as tar:
                members = tar.getmembers()
                print(f"   Files: {len(members)}")

                for member in tqdm(members, desc="Extracting", unit="file"):
                    tar.extract(member, self.output_dir)

            print("✅ Extraction complete")

            # Verify extracted model
            model_dir = self.output_dir / self.model_name
            if not model_dir.exists():
                print(f"❌ ERROR: Expected model directory not found: {model_dir}")
                return False

            onnx_files = list(model_dir.glob("*.onnx"))
            tokenizer_file = model_dir / "tokenizer.json"

            if not onnx_files:
                print(f"❌ ERROR: No ONNX files found in {model_dir}")
                return False

            if not tokenizer_file.exists():
                print(f"❌ ERROR: tokenizer.json not found in {model_dir}")
                return False

            print("✅ Model verified:")
            print(f"   Location: {model_dir}")
            print(f"   ONNX files: {[f.name for f in onnx_files]}")
            print(f"   Tokenizer: {tokenizer_file.name}")

            # Display model size
            total_size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())
            print(f"   Total size: {total_size / 1024 / 1024:.2f} MB ({total_size / 1024 / 1024 / 1024:.2f} GB)")

            return True

        except Exception as e:
            print(f"❌ ERROR: Extraction failed: {e}")
            return False

    def cleanup_downloads(self):
        """Clean up downloaded archive files."""
        try:
            if self.archive_path.exists():
                self.archive_path.unlink()
                print(f"🗑️  Cleaned up: {self.archive_path}")

            if self.checksum_path.exists():
                self.checksum_path.unlink()
                print(f"🗑️  Cleaned up: {self.checksum_path}")

            # Remove download dir if empty
            if self.download_dir.exists() and not any(self.download_dir.iterdir()):
                self.download_dir.rmdir()
                print("🗑️  Removed empty download directory")

        except Exception as e:
            print(f"⚠️  Warning: Cleanup failed: {e}")

    def run(self) -> bool:
        """
        Run the download process.

        Returns:
            True if successful, False otherwise
        """
        print("\n" + "=" * 70)
        print("ONNX Model Downloader")
        print("=" * 70)
        print(f"Model: {self.model_name}")
        print(f"Release: {self.release_tag}")
        print(f"Archive: {self.archive_name}")
        print(f"URL: {self.archive_url}")
        print("=" * 70 + "\n")

        # Step 1: Create download directory
        self.create_download_dir()

        # Step 1.5: Check if archive is split
        print("\n🔍 Checking if archive is split...")
        is_split, split_parts = self.check_if_split()

        # Step 2: Download checksum file
        print("\n📥 Step 1/5: Downloading checksum file...")
        if not self.download_file(self.checksum_url, self.checksum_path, "Checksum"):
            return False

        # Step 3: Download model archive (or parts)
        if is_split:
            print(f"\n📥 Step 2/5: Downloading {len(split_parts)} split parts (this may take a while)...")
            for idx, (part_url, part_file) in enumerate(split_parts, 1):
                print(f"\n   Part {idx}/{len(split_parts)}: {part_file.name}")
                if not self.download_file(part_url, part_file, f"Part {idx}"):
                    return False

            # Step 3.5: Merge parts
            print("\n🔗 Step 3/5: Merging split parts...")
            if not self.merge_split_files([pf for _, pf in split_parts]):
                return False
        else:
            print("\n📥 Step 2/5: Downloading model archive (this may take a while)...")
            if not self.download_file(self.archive_url, self.archive_path, f"Model ({self.archive_name})"):
                return False
            print("\n⏭️  Step 3/5: Skipped (no merge needed)")

        # Step 4: Verify checksum
        print("\n🔍 Step 4/5: Verifying checksum...")
        if not self.verify_checksum(is_split=is_split):
            return False

        # Step 5: Extract archive
        print("\n📦 Step 5/5: Extracting model...")
        if not self.extract_archive():
            return False

        # Step 6: Cleanup
        print("\n🗑️  Cleaning up temporary files...")
        self.cleanup_downloads()

        print("\n" + "=" * 70)
        print("✅ SUCCESS! Model downloaded and ready to use.")
        print("=" * 70)
        print(f"\nModel location: {self.output_dir / self.model_name}")
        print("\nNext steps:")
        print("  1. Run your application with ONNX provider")
        print("  2. The model will be automatically detected")
        print("  3. Enjoy fast INT8 inference!")
        print("=" * 70 + "\n")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download pre-exported ONNX models from GitHub Releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download default model (Llama 3.2 3B INT8)
  python scripts/download_onnx_model.py

  # Download specific model version
  python scripts/download_onnx_model.py --tag model-v1.1.0

  # Download to custom directory
  python scripts/download_onnx_model.py --output ./my-models

  # Skip checksum verification (not recommended)
  python scripts/download_onnx_model.py --skip-checksum

For more information, see:
  - fileorg/llm_classifier/models/README.md
  - https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=ONNXModelDownloader.DEFAULT_MODEL,
        help=f"Model name (default: {ONNXModelDownloader.DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=ONNXModelDownloader.DEFAULT_TAG,
        help=f"GitHub release tag (default: {ONNXModelDownloader.DEFAULT_TAG})",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output directory (default: {ONNXModelDownloader.MODELS_DIR})",
    )

    parser.add_argument(
        "--skip-checksum",
        action="store_true",
        help="Skip checksum verification (not recommended for security)",
    )

    args = parser.parse_args()

    # Create downloader
    downloader = ONNXModelDownloader(
        model_name=args.model,
        release_tag=args.tag,
        output_dir=args.output,
        skip_checksum=args.skip_checksum,
    )

    # Run download
    success = downloader.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
