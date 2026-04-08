from setuptools import setup

setup(
    name="py7zip",
    version="1.1.0",
    description="Python library bundled with pre-compiled 7-Zip binary",
    packages=["py7zip"],
    # This line tells setuptools to include everything inside the py7zip/bin folder
    package_data={"py7zip": ["bin/*"]}, 
    include_package_data=True,
)