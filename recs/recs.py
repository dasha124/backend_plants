import json
import numpy as np



with open('recs/vects_q.npy', 'rb') as f:
  vects = np.load(f)

with open('recs/index.json', 'rb') as f:
  index = json.load(f)

def get_similar(v, vects, n=5):
    scores = np.matmul(vects, v)
    scores = scores / 128
    top_similat_ind = (-scores).argsort()[:n]
    return {
        'similar_ind': list(top_similat_ind),
        'similar_scores': list(scores[top_similat_ind])
    }


def get_by_indexs(inds, index):
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
  return res


def get_sim_mean(viewed_ids, vects):
  n = 5
  v = np.zeros(64)
  viewed_ids = viewed_ids[::-1][:n]
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
