import keras.backend as K
import numpy as np
from keras.layers import Input
from keras.models import Model

from spp.RoiPooling import RoiPooling

dim_ordering = K.image_data_format()
assert dim_ordering in {'channels_last','channels_first'}, 'dim_ordering must be in {channels_last,channels_first}'

pooling_regions = [1, 2, 4]
num_rois = 2
num_channels = 3

if dim_ordering == 'channels_last':
    in_img = Input(shape=(None, None, num_channels))
elif dim_ordering == 'channels_first':
    in_img = Input(shape=(num_channels, None, None))

in_roi = Input(shape=(num_rois, 4))

out_roi_pool = RoiPooling(pooling_regions, num_rois)([in_img, in_roi])

model = Model([in_img, in_roi], out_roi_pool)
model.summary()

model.compile(loss='mse', optimizer='sgd')

for img_size in [8, 16, 32]:

    if dim_ordering == 'channels_first':
        X_img = np.random.rand(1, num_channels, img_size, img_size)
        row_length = [float(X_img.shape[2]) / i for i in pooling_regions]
        col_length = [float(X_img.shape[3]) / i for i in pooling_regions]
    elif dim_ordering == 'channels_last':
        X_img = np.random.rand(1, img_size, img_size, num_channels)
        row_length = [float(X_img.shape[1]) / i for i in pooling_regions]
        col_length = [float(X_img.shape[2]) / i for i in pooling_regions]

    X_roi = np.array([[0, 0, img_size / 1, img_size / 1],
                      [0, 0, img_size / 2, img_size / 2]])

    X_roi = np.reshape(X_roi, (1, num_rois, 4)).astype(int)

    Y = model.predict([X_img, X_roi])

    for roi in range(num_rois):

        if dim_ordering == 'channels_first':
            X_curr = X_img[0, :, X_roi[0, roi, 0]:X_roi[0, roi, 2], X_roi[0, roi, 1]:X_roi[0, roi, 3]]
            row_length = [float(X_curr.shape[1]) / i for i in pooling_regions]
            col_length = [float(X_curr.shape[2]) / i for i in pooling_regions]
        elif dim_ordering == 'channels_last':
            X_curr = X_img[0, X_roi[0, roi, 0]:X_roi[0, roi, 2], X_roi[0, roi, 1]:X_roi[0, roi, 3], :]
            row_length = [float(X_curr.shape[0]) / i for i in pooling_regions]
            col_length = [float(X_curr.shape[1]) / i for i in pooling_regions]

        idx = 0

        for pool_num, num_pool_regions in enumerate(pooling_regions):
            for ix in range(num_pool_regions):
                for jy in range(num_pool_regions):
                    for cn in range(num_channels):

                        x1 = int(round(ix * col_length[pool_num]))
                        x2 = int(round(ix * col_length[pool_num] + col_length[pool_num]))
                        y1 = int(round(jy * row_length[pool_num]))
                        y2 = int(round(jy * row_length[pool_num] + row_length[pool_num]))

                        if dim_ordering == 'channels_first':
                            m_val = np.max(X_curr[cn, y1:y2, x1:x2])
                        elif dim_ordering == 'channels_last':
                            m_val = np.max(X_curr[y1:y2, x1:x2, cn])

                        np.testing.assert_almost_equal(
                            m_val, Y[0, roi, idx], decimal=6)
                        idx += 1
                        
print('Passed roi pooling test')