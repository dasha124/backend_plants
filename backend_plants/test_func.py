# tests.py
import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status

class GetPlantClassesAPITestCase(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('backend_plants.views.Plant_Class')
    @patch('backend_plants.views.GetPlantClassSerializer')
    def test_get_plant_classes(self, MockSerializer, MockPlantClass):
        # Создаем экземпляры для моков
        mock_plant_instance_1 = MagicMock()
        mock_plant_instance_1.plant_class_id = 1
        mock_plant_instance_1.class_name = 'Роза'
        mock_plant_instance_1.image_url_class = 'http://localhost:9000/logo/Роза.png'

        
        mock_plant_instance_2 = MagicMock()
        mock_plant_instance_2.plant_class_id = 2
        mock_plant_instance_2.class_name = 'Лилия'
        mock_plant_instance_2.image_url_class = 'http://localhost:9000/logo/Лилия.png'

        mock_plant_instance_3 = MagicMock()
        mock_plant_instance_3.plant_class_id = 3
        mock_plant_instance_3.class_name = 'Бамбук'
        mock_plant_instance_3.image_url_class = 'http://localhost:9000/logo/Бамбук.png'

        # Настраиваем метод all() так, чтобы он возвращал наши моки
        MockPlantClass.objects.all.return_value = [mock_plant_instance_1, mock_plant_instance_2, mock_plant_instance_3]

        # Настраиваем возврат данных для сериализатораs
        MockSerializer.return_value.data = [
            {'plant_class_id': 1, 'class_name': 'Роза', 'image_url_class':'http://localhost:9000/logo/Роза.png'},
            {'plant_class_id': 2, 'class_name': 'Лилия', 'image_url_class':'http://localhost:9000/logo/Лилия.png'},
            {'plant_class_id': 3, 'class_name': 'Бамбук', 'image_url_class':'http://localhost:9000/logo/Бамбук.png'}
        ]

        # Выполняем GET запрос к API
        response = self.client.get('/api/plants/')  # Замените на актуальный URL вашего API

        # Проверяем статус ответа и данные
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            {'plant_class_id': 1, 'class_name': 'Роза', 'image_url_class':'http://localhost:9000/logo/Роза.png'},
            {'plant_class_id': 2, 'class_name': 'Лилия', 'image_url_class':'http://localhost:9000/logo/Лилия.png'},
            {'plant_class_id': 3, 'class_name': 'Бамбук', 'image_url_class':'http://localhost:9000/logo/Бамбук.png'}
        ])
