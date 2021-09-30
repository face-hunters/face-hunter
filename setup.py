from setuptools import find_packages, setup

setup(
    name='face-hunter',
    packages=find_packages(),
    version='0.1.0',
    description='Our package creates a knowledge graph of entities and videos on YouTube.',
    author='Team Project University of Mannheim',
    license='',
    install_requires=[
        "wget~=3.2",
        "opencv-python~=4.5.1.48",
        "numpy~=1.19.2",
        "pytube==11.0.1",
        "pandas~=1.2.3",
        "nmslib~=2.1.1",
        "scipy~=1.6.1",
        "pip~=21.1",
        "cryptography==2.8",
        "keyring~=10.6.0",
        "requests~=2.23.0",
        "SPARQLWrapper~=1.8.5",
        "levenshtein~=0.12.0",
        "rdflib~=5.0.0",
        "PyYAML~=5.4.1",
        "deepface~=0.0.53",
        "tensorflow~=2.5.0rc1",
        "mtcnn~=0.1.0",
        "matplotlib~=3.1.1",
        "Keras~=2.4.3",
        "ruamel.yaml==0.17.10",
        "pyOpenSSL==19.1.0",
        "gcloud==0.18.3",
        "google-cloud-storage==1.41.0",
        "wikipedia~=1.4.0",
        "flask-ngrok~=0.0.25",
        "facenet-pytorch~=2.4.1"
    ]
)