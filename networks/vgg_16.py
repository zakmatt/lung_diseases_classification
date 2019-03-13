import os

from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from keras.applications.vgg16 import VGG16
from keras.layers import (
    Dense,
    GlobalAveragePooling2D,
    BatchNormalization,
    Conv2D
)
from keras.models import Model
from keras.optimizers import Adam
from utils.loss_validate_callback import LossValidateCallback


# noinspection PyPep8Naming
class VGG16_N(object):
    """

    """

    def __init__(self, img_rows, img_cols, batch_gen,
                 save_model_dir, results_file):

        self.img_rows = img_rows
        self.img_cols = img_cols
        self.batch_gen = batch_gen
        self.model = VGG16_N.model(img_rows=img_rows, img_cols=img_cols)
        self.model.compile(
            optimizer=Adam(lr=1e-4),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        f_path = str(
            save_model_dir
        ) + '/vgg16_batch_' + str(
            batch_gen.batch_size
        ) + '_epoch_{epoch:02d}.hdf5'

        checkpoint = ModelCheckpoint(
            filepath=f_path,
            mode='auto',
            period=1
        )
        self.callbacks = [checkpoint]

        reduce_on_plateau = ReduceLROnPlateau(
            monitor='val_loss', factor=0.8, patience=10, verbose=1,
            mode='auto', min_delta=0.0001, cooldown=5, min_lr=0.0001
        )

        results_file = os.path.join(save_model_dir, results_file)
        self.callbacks = [
            checkpoint,
            reduce_on_plateau,
            LossValidateCallback(
                batch_gen.generate_test_batch,
                results_file
            )
        ]

    @staticmethod
    def model(img_rows, img_cols):
        base_model = VGG16(
            input_shape=(img_rows, img_cols, 3),
            weights='imagenet',
            include_top=False
        )
        base_model.trainable = False

        # add a global spatial average pooling layer
        x = base_model.output
        x = BatchNormalization()(x)
        x = Conv2D(
            64, kernel_size=(1, 1), padding='same',
            activation='relu', name='last_conv'
        )(x)
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu')(x)
        predictions = Dense(3, activation='softmax', name='activations')(x)

        model = Model(inputs=base_model.input, outputs=predictions)

        return model

    def train(self, initial_epoch, nb_epochs, steps_per_epoch):
        self.model.fit_generator(
            self.batch_gen.train_batches,
            steps_per_epoch=steps_per_epoch,
            epochs=nb_epochs,
            callbacks=self.callbacks,
            initial_epoch=initial_epoch,
            validation_data=self.batch_gen.validation_batches,
            validation_steps=self.batch_gen.validate.shape[0]
        )

    def load_weights(self, weights_path):
        self.model.load_weights(weights_path)