from boltons.cacheutils import cachedproperty
import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.python.client import device_lib
from tensorflow.keras.layers import Conv2D, Dense, Dropout, Flatten, Input, MaxPooling2D, Permute, RepeatVector, Reshape, TimeDistributed, Lambda, LSTM, GRU, CuDNNLSTM, Bidirectional
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import Model as KerasModel

from text_recognizer.models.line_model import LineModel
from text_recognizer.networks.lenet import lenet
from text_recognizer.networks.misc import slide_window
from text_recognizer.networks.ctc import ctc_decode


def line_lstm_ctc(input_shape, output_shape, window_width=28, window_stride=14, num_conv=128, num_lstm=256):
    image_height, image_width = input_shape
    output_length, num_classes = output_shape

    num_windows = int((image_width - window_width) / window_stride) + 1
    if num_windows < output_length:
        raise ValueError(f'Window width/stride need to generate at least {output_length} windows (currently {num_windows})')

    image_input = Input(shape=input_shape, name='image')
    y_true = Input(shape=(output_length,), name='y_true')
    input_length = Input(shape=(1,), name='input_length')
    label_length = Input(shape=(1,), name='label_length')

    gpu_present = len(device_lib.list_local_devices()) > 1
    lstm_fn = CuDNNLSTM if gpu_present else LSTM

    # Your code should use slide_window and extract image patches from image_input.
    # Pass a convolutional model over each image patch to generate a feature vector per window.
    # Pass these features through one or more LSTM layers.
    # Convert the lstm outputs to softmax outputs.
    # Note that lstms expect a input of shape (num_batch_size, num_timesteps, feature_length).

    image_reshaped = Reshape((image_height, image_width, 1))(image_input)
    # (image_height, image_width, 1)

    ##### Your code below (Lab 3)
#    ## ORIGINAL CODE (slightly modified)
#    image_patches = Lambda(
#        slide_window,
#        arguments={'window_width': window_width, 'window_stride': window_stride}
#    )(image_reshaped)
#    # (num_windows, image_height, window_width, 1)
#
#    # Make a LeNet and get rid of the last two layers (softmax and dropout)
#    convnet = lenet((image_height, window_width, 1), (num_classes,))
#    convnet = KerasModel(inputs=convnet.inputs, outputs=convnet.layers[-2].output)
#    convnet_outputs = TimeDistributed(convnet)(image_patches)
#    # (num_windows, 128)
#    drop_1 = Dropout(0.25)(convnet_outputs)
#    lstm_output = Bidirectional(lstm_fn(256, return_sequences=True))(drop_1)
#    # (num_windows, 128*2)
#
#    drop_2 = Dropout(0.25)(lstm_output)
#    lstm_output2 = Bidirectional(lstm_fn(256, return_sequences=True))(drop_2)
#    
#    drop_3 = Dropout(0.25)(lstm_output2)
#    softmax_output = Dense(num_classes, activation='softmax',
#                           name='softmax_output')(drop_3)
#    # (num_windows, num_classes)

#    ## UPDATED CODE
#    conv = Conv2D(num_conv, (image_height, window_width), (1, window_stride), activation='relu')(image_reshaped)
#    # (1, num_windows, num_conv)
#    # num_windows = (image_width - window_width) / window_stride + 1
#    
#    conv_squeezed = Lambda(lambda x: K.squeeze(x, 1))(conv)
#    # (num_windows, num_conv)
#    
#    drop_1 = Dropout(0.5)(conv_squeezed)
#    lstm_output = Bidirectional(lstm_fn(num_lstm, return_sequences=True))(drop_1)
#    # (num_windows, num_lstm * 2)
#    
#    drop_2 = Dropout(0.5)(lstm_output)
#    lstm_output2 = Bidirectional(lstm_fn(int(num_lstm/2), return_sequences=True))(drop_2)
#    # (num_windows, num_lstm)
#
#    drop_3 = Dropout(0.5)(lstm_output2)
#    softmax_output = Dense(num_classes, activation='softmax', name='softmax_output')(drop_3)
    # (num_windows, num_classes)
    ## FINISHED UPDATE
    ##### Your code above (Lab 3)

    ##### 2nd winner
#    image_patches = Lambda(
#        slide_window,
#        arguments={'window_width': window_width, 'window_stride': window_stride}
#    )(image_reshaped)
#    # (num_windows, image_height, window_width, 1)
#
#    # Make a LeNet and get rid of the last two layers (softmax and dropout)
#    convnet = lenet((image_height, window_width, 1), (num_classes,))
#    convnet = KerasModel(inputs=convnet.inputs, outputs=convnet.layers[-2].output)
#    convnet_outputs = TimeDistributed(convnet)(image_patches)
#    # (num_windows, 128)
#
#    lstm_output = Bidirectional(lstm_fn(128, return_sequences=True))(convnet_outputs)
#    # (num_windows, 128)
#
#    lstm_output_1_drop_out = Dropout(0.2)(lstm_output)
#    
#    lstm_output2 = Bidirectional(lstm_fn(128, return_sequences=True))(lstm_output_1_drop_out)
#
#    lstm_output_2_drop_out = Dropout(0.2)(lstm_output2)
#
#    softmax_output = Dense(num_classes, activation='softmax', name='softmax_output')(lstm_output_2_drop_out)    
    ##### 2nd winner end
    
    ##### 1st winner
    image_patches = Lambda(
        slide_window,
        arguments={'window_width': window_width, 'window_stride': window_stride}
    )(image_reshaped)
    # (num_windows, image_height, window_width, 1)

    # Make a LeNet and get rid of the last two layers (softmax and dropout)
    convnet = lenet((image_height, window_width, 1), (num_classes,))
    convnet = KerasModel(inputs=convnet.inputs, outputs=convnet.layers[-2].output)
    convnet_outputs = TimeDistributed(convnet)(image_patches)
    # (num_windows, 128)

    convnet_outputs = Dropout(0.5)(convnet_outputs)
    lstm_output = Bidirectional(lstm_fn(256, return_sequences=True))(convnet_outputs)
    convnet_outputs = Dropout(0.5)(convnet_outputs)
    lstm_output = Bidirectional(lstm_fn(256, return_sequences=True))(convnet_outputs)
    lstm_output = Dropout(0.5)(lstm_output)

    softmax_output = Dense(num_classes, activation='softmax', name='softmax_output')(lstm_output)
    ##### 1st winner end
    
    input_length_processed = Lambda(
        lambda x, num_windows=None: x * num_windows,
        arguments={'num_windows': num_windows}
    )(input_length)

    ctc_loss_output = Lambda(
        lambda x: K.ctc_batch_cost(x[0], x[1], x[2], x[3]),
        name='ctc_loss'
    )([y_true, softmax_output, input_length_processed, label_length])

    ctc_decoded_output = Lambda(
        lambda x: ctc_decode(x[0], x[1], output_length),
        name='ctc_decoded'
    )([softmax_output, input_length_processed])

    model = KerasModel(
        inputs=[image_input, y_true, input_length, label_length],
        outputs=[ctc_loss_output, ctc_decoded_output]
    )
    return model

