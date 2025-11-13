import os
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0

# Config - adjust if needed
BASE = os.path.dirname(__file__)
DATA_ROOT = os.path.join(BASE, "dataset")      # supports dataset/train & dataset/val OR dataset/<class>...
TRAIN_DIR = os.path.join(DATA_ROOT, "train")
VAL_DIR = os.path.join(DATA_ROOT, "val")
CLASS_JSON = os.path.join(BASE, "class_index_to_label.json")
MODEL_OUT = os.path.join(BASE, "unified_model.keras")

IMG_SIZE = (224, 224)
BATCH = 32
EPOCHS = 12
SEED = 123

def list_subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

def build_datasets():
    # If dataset/train exists and has subfolders, prefer explicit train/val layout
    train_classes = list_subdirs(TRAIN_DIR)
    val_classes = list_subdirs(VAL_DIR)
    if train_classes:
        class_names = sorted(set(train_classes) | set(val_classes))
        print("Using split folders. Classes:", class_names)
        train_ds = tf.keras.preprocessing.image_dataset_from_directory(
            TRAIN_DIR, labels='inferred', label_mode='categorical',
            class_names=class_names, image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=True)
        if val_classes:
            val_ds = tf.keras.preprocessing.image_dataset_from_directory(
                VAL_DIR, labels='inferred', label_mode='categorical',
                class_names=class_names, image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=False)
        else:
            # If val missing, create validation split from train
            train_ds = tf.keras.preprocessing.image_dataset_from_directory(
                TRAIN_DIR, labels='inferred', label_mode='categorical',
                validation_split=0.2, subset='training', class_names=class_names,
                image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=True)
            val_ds = tf.keras.preprocessing.image_dataset_from_directory(
                TRAIN_DIR, labels='inferred', label_mode='categorical',
                validation_split=0.2, subset='validation', class_names=class_names,
                image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=False)
        return train_ds, val_ds, class_names

    # Fallback: dataset contains class folders directly under DATA_ROOT
    top_level = list_subdirs(DATA_ROOT)
    if top_level:
        class_names = sorted(top_level)
        print("Using single-folder dataset with automatic split. Classes:", class_names)
        ds = tf.keras.preprocessing.image_dataset_from_directory(
            DATA_ROOT, labels='inferred', label_mode='categorical',
            validation_split=0.2, subset='training', class_names=class_names,
            image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=True)
        val_ds = tf.keras.preprocessing.image_dataset_from_directory(
            DATA_ROOT, labels='inferred', label_mode='categorical',
            validation_split=0.2, subset='validation', class_names=class_names,
            image_size=IMG_SIZE, batch_size=BATCH, seed=SEED, shuffle=False)
        return ds, val_ds, class_names

    raise FileNotFoundError("No dataset found. Place class folders under dataset/ or dataset/train & dataset/val")

def prepare(ds, augment=False):
    AUTOTUNE = tf.data.AUTOTUNE
    def _scale(x, y):
        x = tf.image.resize(x, IMG_SIZE)
        # EfficientNet preprocess_input expects float inputs in range [-1,1]
        x = tf.keras.applications.efficientnet.preprocess_input(x)
        return x, y
    ds = ds.map(_scale, num_parallel_calls=AUTOTUNE)
    if augment:
        aug = tf.keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.06),
            layers.RandomContrast(0.06),
        ])
        ds = ds.map(lambda x, y: (aug(x, training=True), y), num_parallel_calls=AUTOTUNE)
    return ds.cache().prefetch(AUTOTUNE)

def build_model(num_classes):
    base = EfficientNetB0(include_top=False, input_shape=(*IMG_SIZE, 3), weights='imagenet')
    base.trainable = False
    inp = layers.Input(shape=(*IMG_SIZE, 3))
    x = base(inp, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation='swish')(x)
    out = layers.Dense(num_classes, activation='softmax')(x)
    model = models.Model(inp, out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-4),
                  loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def main():
    print("Detecting dataset...")
    train_ds, val_ds, classes = build_datasets()
    print("Classes detected:", classes)

    train_ds = prepare(train_ds, augment=True)
    val_ds = prepare(val_ds, augment=False)

    model = build_model(len(classes))
    model.summary()

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(MODEL_OUT, save_best_only=True, monitor='val_loss'),
        tf.keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True, monitor='val_loss'),
        tf.keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5, monitor='val_loss')
    ]

    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, callbacks=callbacks)

    # Optional fine-tune
    base_layer = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) or hasattr(layer, "trainable"):
            base_layer = layer
            break
    if base_layer is not None:
        try:
            base_layer.trainable = True
            model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
                          loss='categorical_crossentropy', metrics=['accuracy'])
            model.fit(train_ds, validation_data=val_ds, epochs=3, callbacks=callbacks)
        except Exception:
            # if fine-tune fails, ignore and continue
            pass

    model.save(MODEL_OUT)
    with open(CLASS_JSON, "w", encoding="utf-8") as f:
        json.dump({i: c for i, c in enumerate(classes)}, f, ensure_ascii=False, indent=2)

    print("Training finished. Model saved to:", MODEL_OUT)
    print("Class map written to:", CLASS_JSON)

if __name__ == "__main__":
    main()