--- 
# 1 тест  
python
'''
train_ds, test_ds = load_datasets(True, False, batch_size=1000)

def create_model():
    # Загружаем MobileNetV2 с предварительно обученными весами (imagenet)
    base_model = tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                                   include_top=False,
                                                   weights='imagenet')

    # Замораживаем веса базовой модели
    base_model.trainable = False

    # Размораживаем последние несколько слоев
    for layer in base_model.layers[-20:]:
        layer.trainable = True

    # Создаем модель
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        # layers.Dense(512, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        # layers.BatchNormalization(),
        # layers.Dropout(0.5),
        # layers.Dense(2048, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        # layers.BatchNormalization(),
        # layers.Dropout(0.5),
        # layers.Dense(1024, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        # layers.BatchNormalization(),
        # layers.Dropout(0.5),
        layers.Dense(LABELS, activation='softmax')
    ])

    # model.compile(optimizer=tf.keras.optimizers.RMSprop(learning_rate=LEARNING_RATE),
    #               loss='sparse_categorical_crossentropy',
    #               metrics=['accuracy'])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    return model
'''
Epoch 1/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 119ms/step - accuracy: 0.2333 - loss: 2.0154
Epoch 1: val_accuracy improved from -inf to 0.33434, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 165s 159ms/step - accuracy: 0.2333 - loss: 2.0153 - val_accuracy: 0.3343 - val_loss: 1.7837 - learning_rate: 1.0000e-05
Epoch 2/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 121ms/step - accuracy: 0.4144 - loss: 1.5942
Epoch 2: val_accuracy improved from 0.33434 to 0.42857, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 158s 158ms/step - accuracy: 0.4144 - loss: 1.5942 - val_accuracy: 0.4286 - val_loss: 1.5566 - learning_rate: 1.0000e-05
Epoch 3/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 119ms/step - accuracy: 0.4738 - loss: 1.4296
Epoch 3: val_accuracy improved from 0.42857 to 0.46016, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 155s 155ms/step - accuracy: 0.4738 - loss: 1.4295 - val_accuracy: 0.4602 - val_loss: 1.4683 - learning_rate: 1.0000e-05
Epoch 4/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 112ms/step - accuracy: 0.5252 - loss: 1.3087
Epoch 4: val_accuracy improved from 0.46016 to 0.47258, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 147s 147ms/step - accuracy: 0.5252 - loss: 1.3087 - val_accuracy: 0.4726 - val_loss: 1.4195 - learning_rate: 1.0000e-05
Epoch 5/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 110ms/step - accuracy: 0.5561 - loss: 1.2306
Epoch 5: val_accuracy improved from 0.47258 to 0.48429, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 143s 143ms/step - accuracy: 0.5561 - loss: 1.2306 - val_accuracy: 0.4843 - val_loss: 1.3854 - learning_rate: 1.0000e-05
Epoch 6/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 109ms/step - accuracy: 0.5800 - loss: 1.1720
Epoch 6: val_accuracy improved from 0.48429 to 0.48997, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 143s 143ms/step - accuracy: 0.5800 - loss: 1.1720 - val_accuracy: 0.4900 - val_loss: 1.3607 - learning_rate: 1.0000e-05
Epoch 7/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 110ms/step - accuracy: 0.5977 - loss: 1.1189
Epoch 7: val_accuracy improved from 0.48997 to 0.49636, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 144s 144ms/step - accuracy: 0.5977 - loss: 1.1189 - val_accuracy: 0.4964 - val_loss: 1.3434 - learning_rate: 1.0000e-05
Epoch 8/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 109ms/step - accuracy: 0.6177 - loss: 1.0780
Epoch 8: val_accuracy improved from 0.49636 to 0.50346, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 143s 143ms/step - accuracy: 0.6177 - loss: 1.0780 - val_accuracy: 0.5035 - val_loss: 1.3307 - learning_rate: 1.0000e-05
Epoch 9/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 109ms/step - accuracy: 0.6464 - loss: 1.0121
Epoch 9: val_accuracy improved from 0.50346 to 0.50453, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 143s 143ms/step - accuracy: 0.6464 - loss: 1.0121 - val_accuracy: 0.5045 - val_loss: 1.3236 - learning_rate: 1.0000e-05
Epoch 10/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 109ms/step - accuracy: 0.6644 - loss: 0.9651
Epoch 10: val_accuracy improved from 0.50453 to 0.51003, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 143s 143ms/step - accuracy: 0.6644 - loss: 0.9651 - val_accuracy: 0.5100 - val_loss: 1.3159 - learning_rate: 1.0000e-05
Epoch 11/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 110ms/step - accuracy: 0.6808 - loss: 0.9177
Epoch 11: val_accuracy improved from 0.51003 to 0.51393, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 144s 144ms/step - accuracy: 0.6808 - loss: 0.9177 - val_accuracy: 0.5139 - val_loss: 1.3080 - learning_rate: 1.0000e-05
Epoch 12/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 110ms/step - accuracy: 0.7056 - loss: 0.8763
Epoch 12: val_accuracy improved from 0.51393 to 0.51961, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 144s 144ms/step - accuracy: 0.7056 - loss: 0.8763 - val_accuracy: 0.5196 - val_loss: 1.3116 - learning_rate: 1.0000e-05
Epoch 13/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 109ms/step - accuracy: 0.7135 - loss: 0.8390
Epoch 13: val_accuracy did not improve from 0.51961
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 148s 148ms/step - accuracy: 0.7135 - loss: 0.8390 - val_accuracy: 0.5185 - val_loss: 1.3077 - learning_rate: 1.0000e-05
Epoch 14/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 122ms/step - accuracy: 0.7380 - loss: 0.7877
Epoch 14: val_accuracy improved from 0.51961 to 0.52245, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 158s 158ms/step - accuracy: 0.7380 - loss: 0.7877 - val_accuracy: 0.5224 - val_loss: 1.3152 - learning_rate: 1.0000e-05
Epoch 15/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 112ms/step - accuracy: 0.7503 - loss: 0.7656
Epoch 15: val_accuracy did not improve from 0.52245

Epoch 15: ReduceLROnPlateau reducing learning rate to 2.9999999242136253e-06.
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 147s 147ms/step - accuracy: 0.7503 - loss: 0.7656 - val_accuracy: 0.5212 - val_loss: 1.3142 - learning_rate: 1.0000e-05
Epoch 16/100
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 0s 114ms/step - accuracy: 0.7702 - loss: 0.7142
Epoch 16: val_accuracy improved from 0.52245 to 0.52316, saving model to model\checkpoints\best_model.keras
1000/1000 ━━━━━━━━━━━━━━━━━━━━ 151s 151ms/step - accuracy: 0.7702 - loss: 0.7142 - val_accuracy: 0.5232 - val_loss: 1.3137 - learning_rate: 3.0000e-06
Epoch 16: early stopping
Restoring model weights from the end of the best epoch: 13.
Модель сохранена!
История обучения: {'accuracy': [0.2910727560520172, 0.4207301735877991, 0.4795573949813843, 0.5243811011314392, 0.5537634491920471, 0.5795823931694031, 0.6004000902175903, 0.6240310072898865, 0.645911455154419, 0.662102997303009, 0.6824206113815308, 0.7012377977371216, 0.717929482460022, 0.7301825284957886, 0.7479369640350342, 0.7732558250427246], 'loss': [1.8817460536956787, 1.5593016147613525, 1.4124760627746582, 1.3103772401809692, 1.2327419519424438, 1.1717811822891235, 1.1165165901184082, 1.059722661972046, 1.0093286037445068, 0.9718832969665527, 0.9230145215988159, 0.8795625567436218, 0.8387959599494934, 0.8035825490951538, 0.7625089287757874, 0.7111309766769409], 'val_accuracy': [0.3343389630317688, 0.4285714328289032, 0.4601597189903259, 0.472582072019577, 0.484294593334198, 0.48997336626052856, 0.49636203050613403, 0.5034605264663696, 0.5045253038406372, 0.5100266337394714, 0.5139307975769043, 0.5196095705032349, 0.5185447931289673, 0.5224489569664001, 0.5212067365646362, 0.523158848285675], 'val_loss': [1.7836617231369019, 1.5566459894180298, 1.4682878255844116, 1.419500470161438, 1.385386347770691, 1.360694408416748, 1.3433657884597778, 1.3306663036346436, 1.3235502243041992, 1.315912127494812, 1.3079743385314941, 1.311570644378662, 1.3076646327972412, 1.3152140378952026, 1.3141840696334839, 1.3136956691741943], 'learning_rate': [9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 9.999999747378752e-06, 2.9999998787388904e-06]}
Лучший результат: 0.5232 на эпохе 16
