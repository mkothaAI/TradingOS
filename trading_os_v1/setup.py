from setuptools import setup, find_packages

setup(
    name='trading_os_v1',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'httpx',
        'numpy',
        'pandas',
        'pydantic',
        'python-dotenv',
        'scipy',
        'uvicorn'
    ],
    python_requires='>=3.8',
)
