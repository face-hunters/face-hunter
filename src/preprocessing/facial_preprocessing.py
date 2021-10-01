import numpy as np
import cv2
from tensorflow.keras.preprocessing.image import img_to_array
import matplotlib.pyplot as plt


def face_alignment(img, shape, keypoints, blank=0.3, show=False):
    """ Aligns an image according to keypoints.

    Args:
        img (cv2 Image): The original image.
        shape(tuple): Tuple of two floats that show the target image shape.
        keypoints (dict): The coordinates of the detected face. (left_eye, right_eye, mouth_left, mouth_right).
        blank (float): Scaling Parameter.
        show (bool): Whether  the aligned Image should be displayed or not.

    Returns:
        img_pixels (cv2 Image): Aligned Image
    """
    left_eye = keypoints['left_eye']
    right_eye = keypoints['right_eye']
    mouth_left = keypoints['mouth_left']
    mouth_right = keypoints['mouth_right']

    eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
    mouth_center = ((mouth_left[0] + mouth_right[0]) // 2, (mouth_left[1] + mouth_right[1]) // 2)

    # get rotation angle
    dY = right_eye[1] - left_eye[1]
    dX = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dY, dX))

    # get scale by the distance from eye center to mouth center
    desiredDist = (1 - 2 * blank) * shape[1]
    dY = mouth_center[1] - eye_center[1]
    dX = mouth_center[0] - eye_center[0]
    dist = np.sqrt((dX ** 2) + (dY ** 2))
    scale = desiredDist / dist

    M = cv2.getRotationMatrix2D(eye_center, angle, scale)

    # translation
    tX = shape[0] * 0.5
    tY = shape[1] * blank
    M[0, 2] += (tX - eye_center[0])
    M[1, 2] += (tY - eye_center[1])

    aligned_face = cv2.warpAffine(img, M, shape, flags=cv2.INTER_CUBIC)

    if show:
        plt.imshow(aligned_face)
        plt.show()

    # input layer shape
    # img_pixels = img_to_array(aligned_face)
    # img_pixels = np.expand_dims(aligned_face, axis=0)
    # img_pixels = img_pixels / 255
    img_pixels = aligned_face / 255

    return img_pixels
