from setuptools import setup, find_packages
from pathlib import Path


def find_stubs(path: Path):
    stubs = [str(pyi.relative_to(path)) for pyi in path.rglob("*.pyi")]
    print(f"Found stubs: {stubs}")  # Debug
    return stubs

# Check what files setup.py sees
print("Packages found:", find_packages())
print("Files in dp/:", list(Path("dp").rglob("*")))


setup(
    name='dp',
    version='0.1',
    packages=find_packages(),
    package_data={"dp": [*find_stubs(path=Path("dp"))]},
    include_package_data=True
)

