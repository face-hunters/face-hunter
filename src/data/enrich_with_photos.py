import os
import time
import re
import logging
import urllib.request
import urllib.error
from urllib.parse import quote
from multiprocessing import Pool
from user_agent import generate_user_agent
import io
import face_recognition
import cv2
import numpy as np
from PIL import Image
import logging
from io import BytesIO
from PIL import Image
from IPython.display import Image
from multiprocessing import Pool

log_file = 'download.log'
logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+", format="%(asctime)-15s %(levelname)-8s  %(message)s")


def download_page(url):
    """download raw content of the page
    
    Args:
        url (str): url of the page 
    
    Returns:
        raw content of the page
    """
    try:
        headers = {}
        headers['User-Agent'] = generate_user_agent()
        headers['Referer'] = 'https://www.google.com'
        req = urllib.request.Request(url, headers = headers)
        resp = urllib.request.urlopen(req)
        return str(resp.read())
    except Exception as e:
        print(f'error while downloading page {url}')
        logging.error(f'error while downloading page {url}')
        return None


def parse_page(url):
    """parge the page and get all the links of images, max number is 100 due to limit by google
    
    Args:
        url (str): url of the page
    
    Returns:
        A set containing the urls of images
    """
    page_content = download_page(url)
    if page_content:
        link_list = re.findall('src="(.*?)"', page_content)
        if len(link_list) == 0:
            print(f'got 0 links from page {url}')
            logging.info(f'got 0 links from page {url}')
            return set()
        else:
            return set(link_list)
    else:
        return set()


def create_image_links(main_keyword, supplemented_keywords):
    image_links = set()
    for i_keyword, _ in enumerate(supplemented_keywords):
        print(f'Process {os.getpid()} supplemented keyword: {supplemented_keywords[i_keyword]}')
        search_query = quote(main_keyword + ' ' + supplemented_keywords[i_keyword])
        url = 'https://www.google.com/search?q=' + search_query + '&source=lnms&tbm=isch'
        image_links = image_links.union(parse_page(url))
        print(f'Process {os.getpid()} got {len(image_links)} links so far')
        time.sleep(2)
    return image_links


def fetch_image(link):
    req = urllib.request.Request(link, headers = {"User-Agent": generate_user_agent()})
    response = urllib.request.urlopen(req)
    return response.read()


def encode_downloaded_img(img):
    temp_img = Image.open(io.BytesIO(img))
    temp_img = cv2.cvtColor(np.array(temp_img), cv2.COLOR_RGB2BGR)
    encodings = face_recognition.face_encodings(temp_img)
    if len(encodings) != 1:
        print('passing', len(encodings))
        return []
    return encodings[0]


def compare_install_face(img, img_dir, downloaded, encode=None):
    try:
        encode_new_img = encode_downloaded_img(img)
        if not encode is None and len(encode_new_img) == 128:
            results = face_recognition.compare_faces([encode], encode_new_img)
            print(results)
            if results[0]:
                file_path = os.path.join(img_dir, f'{2+downloaded}.jpg')
                with open(file_path,'wb') as wf:
                    wf.write(img)
                downloaded += 1
            else:
                pass
        if encode is None and len(encode_new_img) == 128:
            file_path = os.path.join(img_dir, f'{2+downloaded}.jpg')
            with open(file_path,'wb') as wf:
                wf.write(img)
            downloaded+=1
    except Exception as e:
        print('error', e)
        return downloaded
    return downloaded


def download_images(path, main_keyword, supplemented_keywords, download_dir, num_images, encode=None):
    """download images with one main keyword and multiple supplemented keywords
    
    Args:
        main_keyword (str): main keyword
        supplemented_keywords (list[str]): list of supplemented keywords
    
    Returns:
        None
    """  
    
    print(f'Process {os.getpid()} Main keyword: {main_keyword}')

    img_dir = os.path.join(path, main_keyword)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    image_links = create_image_links(main_keyword, supplemented_keywords)
    print (f"Process {os.getpid()} got totally {len(image_links)} links")
    print ("Start downloading...")

    downloaded = 0
    for i_link, link in enumerate(image_links):
        if downloaded < num_images and i_link < len(image_links):
            print(link)
            img = fetch_image(link)
            file_path = os.path.join(img_dir, f'{i_link}.jpg')
            # my_bytes_io.seek(0)
            downloaded = compare_install_face(img, img_dir, downloaded, encode)
        else:
            break

    print(f"Finish downloading, total {downloaded} downloads")
    

def get_face_encoding(entity):
    # print(os.path.join('data',entity))
    files = os.listdir(os.path.join('data',entity))
    img_name = [i_file for i_file in files if '.jpg' in i_file]
    img_name = img_name[0]
    print(img_name)
    # print(os.listdir(os.path.join('data',entity)))
    img = cv2.imread(os.path.join('data', entity, img_name))
    print(entity)
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2RGB)
    encode = face_recognition.face_encodings(img)[0]
    return encode


def download_thumbnails_entity_list(download_dir, entity_list, num_images, enrich=True):
    supplemented_keywords = ['face']
    p = Pool() # number of process is the number of cores of your CPU
    for i_entity, entity in enumerate(entity_list):
        try:
            if enrich:
                encode = get_face_encoding(entity)
                download_images(download_dir, entity, supplemented_keywords, download_dir, num_images, encode)
            else:
                download_images(download_dir, entity, supplemented_keywords, download_dir, num_images)
            # p.apply_async(download_images, args=(download_dir, entity, supplemented_keywords, download_dir, num_images, encode))
        except Exception as e:
            print(e)
            continue
    p.close()
    p.join()
    print('All fininshed')


def enrich_with_google_photos(thumbnails_path, num_images, enrich=True):
    entity_list = os.listdir(thumbnails_path)
    download_thumbnails_entity_list(thumbnails_path, entity_list, num_images, enrich)