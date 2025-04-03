from django.shortcuts import render  
from django.core.files.storage import FileSystemStorage  
import numpy as np  
from PIL import Image  
from io import BytesIO  
import base64  
from rest_framework.decorators import api_view 
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from backend_plants_app.models import *
from Backend_plants.serializers import *
from django.db.models import Q

imageClassList = {0: 'алоэ', 1: 'бархатцы', 2: 'вербена', 3: 'герань', 4: 'гиацинт', 5: 'глициния', 6: 'декоративная трава',\
           7: 'дуб', 8: 'ель', 9: 'жимолость', 10: 'ирис', 11: 'кактус', 12: 'клематис', 13: 'клен', 14: 'космея', 15: 'лилии', \
            16: 'можжевельник', 17: 'монарда', 18: 'нарцисс', 19: 'орхидея', 20: 'папоротники', 21: 'пион', 22: 'плющ',\
            23: 'рододендрон', 24: 'сансевиерия', 25: 'сосна', 26: 'суккулент', 27: 'тюльпан', 28: 'циния', 29: 'эхинацея', 30: 'яблоня'}


def scoreImagePage(request):  
    return render(request, 'scorepage.html')  

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def predictImage(request):
    base64_str = request.data.get('filePath')
    modelName = request.POST.get('modelName')
    # scorePrediction, img_uri = predictImageData(modelName, '.'+filePathName)
    # scorePrediction 
    serialized_plants_data = predictImageData(modelName, base64_str)
    # context = {'scorePrediction': scorePrediction, 'filePathName': filePathName, 'img_uri': img_uri}  
    # return render(request, 'scorepage.html', context)
    
        # {'scorePrediction': scorePrediction}
    # return render(request, 'scorepage.html', context)
    # return context
    return Response(serialized_plants_data)


def predictImageData(modelName, base64_str):

    image_data = base64.b64decode(base64_str)
    img = Image.open(BytesIO(image_data)).convert("RGB")
    resized_img = img.resize((320, 320), Image.LANCZOS)
    img = np.asarray(img.resize((32, 32), Image.LANCZOS))
      
    try:
        import onnxruntime
    except ModuleNotFoundError:
            print("!!!!!!!!")
            score = "глициния"
            
            return ({"type": score})
    sess = onnxruntime.InferenceSession(r'/home/darya/Документы/GitHub/backend_plants/Backend_plants/media/model/cifar100_5.onnx')
    outputOFModel = np.argmax(sess.run(None, {'input': np.asarray([img]).astype(np.float32)}))
    print(sess.run(None, {'input': np.asarray([img]).astype(np.float32)}))
    print(outputOFModel)


    print("!!!!!!!!")
    score = imageClassList[outputOFModel]
    print("score =", score)

    plants = Plant.objects.all()
    plants = plants.filter(
        Q(plant_name__icontains = score.lower()),
        Q(status='a')
    )

    serializer = GetPlantShortInfoSerializer(plants, many=True)
    # return serializer.data
    response_data = {
        "type": score,
        "plants": serializer.data
    }
    return (response_data)

  
def to_numpy(tensor):  
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()  
  
def to_image(numpy_img):  
    img = Image.fromarray(numpy_img, 'RGB')  
    return img  
  