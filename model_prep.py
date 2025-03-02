import random

# function to segment eeg data based on sampling freq(Hz), window_size(s), and window_shift(s)
def segmentation(signal, sampling_freq=125, window_size=1, window_shift=0.016):
  w_size = int(sampling_freq * window_size)
  w_shift = int(sampling_freq * window_shift)
  segments = []
  i = 0
  while i + w_size <= signal.shape[1]:
    segments.append(signal[:, i: i + w_size])
    i += w_shift
  return segments

def preprocess(signals):
  all_segments = []
  # preprocess signals
  for i, arr in enumerate(signals):
    filtered = arr
    norm_filtered = (filtered - filtered.mean(1, keepdims=True)) / filtered.std(1, keepdims=True)
    segments = segmentation(norm_filtered, 256, 1, 0.04)
    all_segments.extend(segments)
  return all_segments

def balancing(*args, p=1):
  # lists for each target class are passed in for args
  # shuffle each list
  [random.shuffle(data) for data in args]
  # cut off num is int(p * minimum length of any of the lists)
  cutoff_num = int(p * min(list(map(len, args))))
  # slice only up to cut off num for each list
  lists = [x[:cutoff_num] for x in args]
  return lists