import setuptools

with open('README.md') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="queenbee",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="Ladybug Tools",
    author_email="info@ladybug.tools",
    description="Queenbee is a workflow language and a package manager for creating "
    "DAG workflows which empowers all workflow libraries in Ladybug Tools!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pollination/queenbee",
    packages=setuptools.find_packages(exclude=["tests", "docs"]),
    install_requires=requirements,
    extras_require={
        'cli': ['click>=7.0', 'click_plugins==1.1.1']
    },
    entry_points={
        "console_scripts": ["queenbee = queenbee.cli:main"]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    license="MIT"
)
