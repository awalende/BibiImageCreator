.. BibiCreator documentation master file, created by
   sphinx-quickstart on Thu Feb  1 13:22:25 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to BibiCreator's documentation!
=======================================

The documentation is seperated into two pieces:

* BibiCreator logic (this documentation)
* REST Documentation (all functions in src.API)

| You can access the latter within the bibicreator environment 
| by pointing your browser to:
| https://<bibicreator-url>/apidocs

Further information in:

* https://wiki.cebitec.uni-bielefeld.de/bibiserv-1.25.2/index.php/BibiCreator (restricted)





Introduction
============

BibiCreator is a python-flask based webframework for creating linux based images in the OpenStack-Cloud.
It makes use of Ansible and Packer for the provisioning of new images.

Right now it is only useable in the denBI Cloud (Location: University of Bielefeld).

If you would like to test this application, use the designated docker container or an Ansible Role.

* Dockerfile https://github.com/awalende/BibiImageCreator/tree/master/DOCKER
* DockerHUB https://hub.docker.com/r/alexwalender/bibicreator/
* Ansible Role https://github.com/awalende/bibicreator-ansible
* Ansible Role (Galaxy): https://galaxy.ansible.com/awalende/bibicreator-ansible/


Follow the steps documented in those links.



Documentation
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Author
======
B.Sc. Alex Walender CeBiTec Bielefeld


Links
=====

* https://www.ansible.com
* https://www.packer.io
* https://www.denbi.de
