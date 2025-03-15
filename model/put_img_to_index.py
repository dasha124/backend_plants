import torch
from torchvision import models
import torchvision.transforms.functional as transform
import PIL
import os
from tqdm import tqdm
import json
import numpy as np
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image

def put_img_to_index(image_data, image_name):
    print("image_data = ", image_data )
    
    class Identify(torch.nn.Module):
        def __init__(self):
            super().__init__()

        def forward(self, x):
            return x
        
    model = torch.hub.load("chenyaofo/pytorch-cifar-models", 'cifar100_resnet20', pretrained=True)
    num_classes = 31
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features=in_features, out_features=num_classes, bias=True)
    state_dict = torch.load('/home/darya/Документы/GitHub/backend_plants/model/my_model.pth')

    new_state_dict = {}
    for key, value in state_dict.items():
        if key.startswith('1.'):
            new_key = key[2:]
        else:
            new_key = key
            
    if new_key in model.state_dict() and value.size() == model.state_dict()[new_key].size():
        new_state_dict[new_key] = value
    
    model.load_state_dict(new_state_dict, strict=False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    model.fc = Identify()
    height_width = 32
    preprocess = transforms.Compose([
        transforms.Resize((height_width, height_width), interpolation=Image.LANCZOS),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5074, 0.4867, 0.4411], std=[0.2011, 0.1987, 0.2025])
    ])

    model.eval()
    
    # img_path = './recs'
    pil_img = Image.open(image_data).convert('RGB')
    img_transformed = preprocess(pil_img)
    imgs = [img_transformed]

    index = [image_name]
    file_path = './recs/index_1.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            if content:  # Проверяем, что файл не пустой
                existing_index = json.loads(content)
            else:
                existing_index = []
    else:
        existing_index = []

    print('\n######################################################################################################################################\n')
    print("existing_index")
    print(existing_index, len(existing_index))
    updated_index = existing_index.copy()  # Создаем копию существующего индекса
    for item in index:
        if item not in updated_index:  # Проверяем, есть ли элемент уже в списке
            updated_index.append(item) 
    print('\n######################################################################################################################################\n')
    print("updated_index")
    print(updated_index, len(updated_index))

    with open(file_path, 'w') as f:
        json.dump(updated_index, f)

    batch = torch.vstack(tuple((im.unsqueeze(0) for im in imgs)))
    # batch.shape # N.3.224.224
    # print(batch.shape) # [1, N] -массив
    
    with torch.no_grad():
        vects = model(batch)
    print("vects.shape", vects.shape)


    vects_norm = vects / torch.Tensor.repeat(vects.norm(dim=1).unsqueeze(1), 1, 64)
    vects_norm_np = vects_norm.numpy()

    file_path = './recs/vects_1.npy'
    new_vectors = vects_norm_np

    if os.path.exists(file_path):
        existing_vectors = np.load(file_path)
        combined_vectors = np.concatenate((existing_vectors, new_vectors), axis=0)
    else:
        combined_vectors = new_vectors

    with open(file_path, 'wb') as f:
        np.save(f, combined_vectors)
