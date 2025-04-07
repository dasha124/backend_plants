import json
import numpy as np


# try:
#     with open('recs/vects_1.npy', 'rb') as f:
#              vects = np.load(f)
# except EOFError:
#     print("Ошибка: файл 'vects_1.npy' пуст или поврежден.")
# except Exception as e:
#     print(f"Произошла ошибка при загрузке 'vects_1.npy': {e}")

# # Загрузка JSON
# try:
#     with open('recs/index_1.json', 'r') as f:
#         index = json.load(f)
# except json.JSONDecodeError:
#     print("Ошибка: файл 'index_1.json' имеет некорректный формат JSON.")
# except Exception as e:
#     print(f"Произошла ошибка при загрузке 'index_1.json': {e}")


with open('recs/vects_1.npy', 'rb') as f:
  vects = np.load(f)

with open('recs/index_1.json', 'rb') as f:
  index = json.load(f)

def get_similar(v, vects, n):
    scores = np.matmul(vects, v)
    scores = scores / 128
    top_similat_ind = (-scores).argsort()[:n]
    print("top_similat_ind =", top_similat_ind)
    print("scores", scores[top_similat_ind])
    return {
        'similar_ind': list(top_similat_ind),
        'similar_scores': list(scores[top_similat_ind])
    }


def get_by_indexs(inds, index):
    with open('recs/index_1.json', 'rb') as f:
        index = json.load(f)
    f_names = []
    for i in inds:
        f_names.append(f'/pics/{index[i]}_0.jpg')
    return f_names


def filter_(recs, viewed_ids):
    res = {
        'similar_ind': [],
        'similar_scores': []
    }
    for i in range(len(recs['similar_ind'])):
        if recs['similar_ind'][i] not in viewed_ids:
            res['similar_ind'].append(recs['similar_ind'][i])
            res['similar_scores'].append(recs['similar_scores'][i])
        else:
            print("повторяющийся индекс =", recs['similar_ind'][i])
    return res


def get_sim_mean(viewed_ids, vects):
    n = 5
    v = np.zeros(64)
    viewed_ids = viewed_ids[::-1][:n]
    print("viewed_ids =", viewed_ids)
    for i in viewed_ids[:]:
        v += vects[i]
    v /= len(viewed_ids)
    v /= np.linalg.norm(v)
    return filter_(get_similar(v, vects, n+len(viewed_ids)), viewed_ids)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
