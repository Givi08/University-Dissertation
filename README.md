# Positional Encoders for Sign Language Production
This is an implementation of Ben Saunder's Progressive Transformer paper. <br>

Requirements are avilable at: 

`py --3.xy -m pip install -r requirements.txt`

To run this file simply type:

`python __main__.py train ./Configuration.yaml` 

To edit the some of the hyperparamater setup simply modify the `Configuration.yaml` file.

To edit which model is being run go to <a ref = "model.py">model.py</a> and serch for "EDIT HERE". This will allow you to comment out and uncomment the various Encoders used. 

Data is avalable from Adam George's <a href="https://drive.google.com/file/d/11jrpbTVnSMU0_4_3GGZwU6mipWA93moQ/view" title="Google Drive">Google Drive</a>