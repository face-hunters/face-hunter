# Face-Hunter

## Installation
 - Follow instructions of https://github.com/ageitgey/face_recognition 
   (Make sure that dlib and cmake are installed)
 - Install requirements `pip install requirements.txt`


## Architecture

### cli.py
 - Defines the user interface
 - Can be used like `python cli.py <command> <params>`
 
 Currently supports:
###### `run_detection (--path <path to images/videos> --thumbnails <path to thumbnails>)`
###### `download_thumbnails`
###### `download_video_datasets (--path <path to save the dataset at> --dataset <imdb-wiki/imdb-faces/youtube-faces-db/yt-celebrity)`
###### `youtube (--url <path to txt with urls> --path <path to store the videos at>)`

### data.py
 - The script to download videos/images and bring them in a homogeneous format for further calculation 
 the accuracy
 - We need this homogeneous format to work with multiple datasets
 - Downloads the files and creates an information.csv at the top of the folder
 - Structure of the information.csv is: filename, entities (that appear in the file)
 - TODO: implement script to download thumbnails and bring them in a homogeneous format
 
### hunter.py
 - Class that handles the face recognition
 - **fit(thumbnails_path: str)** function creates embeddings of thumbnails or loads existing ones
 - for a fast search over thousands of embeddings a k-Nearest Neighbor Algorithm is trained with the embeddings
 - **predict(information_csv_path: str)** function takes as input the path to a information.csv and returns a list of predicted entities
 - **save(path: str)** function locally saves the created embeddings to reuse them later
 - Parameters of the object allow configuration of the kNN-algorithm and face recognition tool
 
### helpers.py
 - **check_path** function checks if a path exists and creates it otherwise
 