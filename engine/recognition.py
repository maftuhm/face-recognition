import logging

import numpy as np
import torch

from engine.models.mtcnn import MTCNN
from engine.models.inception_resnet_v1 import InceptionResnetV1
from engine.models.utils.functional import to_tensor


class FaceRecognizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceRecognizer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        if self._initialized:
            return
        try:
            self.detector = MTCNN(
                image_size=160, margin=0, min_face_size=20,
                thresholds=[0.6, 0.7, 0.7], factor=0.709,
                post_process=True, keep_all=True, device=device
            )
            self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
            self.threshold = 0.95
            self._initialized = True
        except Exception as e:
            raise RuntimeError("Error initializing FaceRecognizer: {}".format(str(e)))

    @staticmethod
    def distance(embedding1, embedding2):
        return np.linalg.norm(embedding1 - embedding2)

    def encode(self, image):

        batch_mode = True
        if (
                not isinstance(image, (list, tuple)) and
                not (isinstance(image, np.ndarray) and len(image.shape) == 4) and
                not (isinstance(image, torch.Tensor) and len(image.shape) == 4)
        ):
            image = [image]
            batch_mode = False

        embedding = []
        for img in image:

            faces_im, probs = self.detector(img, return_prob=True)
            if faces_im is None:
                continue

            faces = []
            for face, prob in zip(faces_im, probs):
                if prob < self.threshold:
                    continue
                faces.append(face)

            if len(faces) == 0:
                continue

            faces = torch.stack(faces)

            emb = self.resnet(faces).detach().numpy()
            embedding.append(emb)

        if len(embedding) == 0:
            return []

        if not batch_mode:
            embedding = embedding[0]

        return embedding

    def compare(self, references, hypothesis, tolerance=1.045):

        if not isinstance(references, np.ndarray):
            references = np.array(references)

        if not isinstance(hypothesis, np.ndarray):
            hypothesis = np.array(hypothesis)

        scores = [self.distance(reference, hypothesis) for reference in references]
        score = np.mean(scores)
        return score <= tolerance, score


if __name__ == "__main__":
    import os
    from PIL import Image

    face_recognizer = FaceRecognizer()
    # image = Image.open("/Users/maftuh/Downloads/1_nxansq9S1TA9dTfhVCy2LQ.jpg")
    # data = face_recognizer.encode(image)
    # print(len(data))

    data_dir = "/Users/maftuh/Downloads/"
    img_list = ["1_nxansq9S1TA9dTfhVCy2LQ.jpg", "IMG_1043-min.jpeg", "maftuh2.jpeg", "maftuh.jpeg", "WhatsApp Image 2023-12-13 at 02.12.05.jpeg",
                "atta-halilintar.jpeg", "img_face_mask.jpg", "image_T9.jpg", "FT5563fakAApbl9.jpg",
                "Foto-Selfie-Beauty-Zenfone-4-Selfie-Lite.jpg"]

    images = []
    for filename in img_list[:3]:
        img_path = os.path.join(data_dir, filename)
        img = Image.open(img_path)
        images.append(img)

    res = face_recognizer.encode(images)

    for r in res:
        print(r.shape)

        # print(res.shape)
        # images.append(img)

    # result = face_recognizer.encode_batch(images)
    # print(result)
