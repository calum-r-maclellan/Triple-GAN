# Baseline
python train_classifier.py ./configs/classifier_cifar10_mt_aug.yaml -subfolder newbaseline
python train_classifier.py ./configs/classifier_cifar10_mt_noaug.yaml -subfolder newbaseline -key noaug
python train_classifier.py ./configs/classifier_svhn_mt_aug.yaml -subfolder newbaseline
python train_classifier.py ./configs/classifier_svhn_mt_noaug.yaml -subfolder newbaseline -key noaug

python train_gan.py ./configs/gan.yaml -dataset cifar10 -key test -gpu 1
python train_triplegan.py ./configs/triple_gan_svhn.yaml -dataset svhn -key fix_aug.addcgen.testlog -gpu 5
python train_triplegan.py ./configs/triple_gan_svhn.yaml -dataset svhn -key cford_int -gpu 1


python train_triplegan_mt_svhn.py ./configs/triple_gan_mt_svhn.yaml -dataset svhn -subfolder tganmt -translate 0 -gpu 0
python train_triplegan_mt_svhn.py ./configs/triple_gan_mt_svhn.yaml -dataset svhn -subfolder tganmt -translate 2 -gpu 1


python test_triplegan.py ./configs/triple_gan_svhn.yaml -dataset svhn -key test -old_model "/home/kunxu/Workspace/Triple-GAN/allresults/(train_triplegan.py)_(svhn)_(2020-06-12-11-24-49)_()_(cford_int)/models/model209000.pt" -gpu 1