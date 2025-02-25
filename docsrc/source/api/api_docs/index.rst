=========
API Docs
=========

**Init module for MCT API.**

.. literalinclude:: ../../../../tutorials/example_keras_mobilenet.py
    :language: python
    :lines: 16

Functions
=========
- :ref:`pytorch_post_training_quantization<ug-pytorch_post_training_quantization>`: Function to use for post training quantization of Pytorch models.
- :ref:`keras_post_training_quantization<ug-keras_post_training_quantization>`: Function to use for post training quantization of Keras models.
- :ref:`keras_post_training_quantization_mixed_precision<ug-keras_post_training_quantization_mixed_precision>`: Function to use for mixed-precision post training quantization of Keras models (experimental).
- :ref:`get_keras_gptq_config<ug-get_keras_gptq_config>`: Function to create a GradientPTQConfig instance to use for Keras models when using GPTQ (experimental).
- :ref:`get_model<ug-get_model>`: Function to get a hardware model for Tensorflow and Pytorch.

Modules
=========
- :ref:`quantization_config<ug-quantization_config>`: Module to configure the quantization process.
- :ref:`mixed_precision_quantization_config<ug-mixed_precision_quantization_config>`: Module to configure the quantization process when using mixed-precision PTQ.
- :ref:`network_editor<ug-network_editor>`: Module to edit your model during the quantization process.
- :ref:`hardware_representation<ug-hardware_representation>`: Module to create and model hardware-related settings to optimize the model according to, by the hardware the optimized model will use during inference.

Classes
=========
- :ref:`GradientPTQConfig<ug-GradientPTQConfig>`: Class to configure GradientPTQC options for gradient based post training quantization.
- :ref:`FolderImageLoader<ug-FolderImageLoader>`: Class to use an images directory as a representative dataset.
- :ref:`FrameworkInfo<ug-FrameworkInfo>`: Class to wrap framework information to be used by MCT when optimizing models.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. note:: This documentation is auto-generated using Sphinx

