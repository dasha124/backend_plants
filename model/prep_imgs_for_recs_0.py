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




# Загрузка первоначальной модели с предобученными весами
model = torch.hub.load("chenyaofo/pytorch-cifar-models", 'cifar100_resnet20', pretrained=True)

num_classes = 31

in_features = model.fc.in_features  # количество входных признаков для полносвязного слоя
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

print(model)
print('\n######################################################################################################################################\n')
print(model.fc)


# тождественное преобразование
class Identify(torch.nn.Module):
  def __init__(self):
    super().__init__()

  def forward(self, x):
    return x

model.fc = Identify()

height_width = 32
preprocess = transforms.Compose([
    transforms.Resize((height_width, height_width), interpolation=Image.LANCZOS),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5074, 0.4867, 0.4411], std=[0.2011, 0.1987, 0.2025])
])



img_path = '/home/darya/Документы/GitHub/backend_plants/recs/pics'

pil_img = Image.open(f"{img_path}/Вербена прерийная.jpeg").convert('RGB')
print("pil_img.shape #####################################################################################")
img_transformed = preprocess(pil_img)
print(img_transformed.shape)
print('\n######################################################################################################################################\n')

# модель -  врежим вычисления, а не обучения
model.eval()


batch_img = img_transformed.unsqueeze(0)
print("batch_img.shape #####################################################################################")
# batch_img.shape # 1.3.224.224
print(batch_img.shape)
print('\n######################################################################################################################################\n')




with torch.no_grad():
  prediction = model(batch_img)
print("prediction.shape #####################################################################################")
print(prediction.shape) # [1, N] -массив
print('\n######################################################################################################################################\n')

files = os.listdir(img_path)
len(files)

imgs = []

for f in tqdm(files):
  pil_img = PIL.Image.open(f'{img_path}/{f}').convert('RGB')
  # img = transform.to_tensor(pil_img)
  img_transformed = preprocess(pil_img)
  imgs.append(img_transformed)

print("len(imgs) = ", len(imgs))


index = []
for f in files:
  index.append(f.split('.')[0])

with open('./recs/index_1.json', 'w') as f:
  json.dump(index, f)

print(index[9])


batch = torch.vstack(tuple((im.unsqueeze(0) for im in imgs)))
# batch.shape # N.3.224.224
print(batch.shape) # [1, N] -массив
print('\n######################################################################################################################################\n')


with torch.no_grad():
  vects = model(batch)

print("vects.shape", vects.shape)


vects_norm = vects / torch.Tensor.repeat(vects.norm(dim=1).unsqueeze(1), 1, 64)
vects_norm_np = vects_norm.numpy()

with open('./recs/vects_1.npy', 'wb') as f:
  np.save(f, vects_norm_np)