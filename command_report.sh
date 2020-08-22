# 
# see 819 and 820 every day
# 
# learning rate annealing
# 

# baselien cifar10 rerun for both settings
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder 820_D_CI -n_labels 4000 -translate 2 -flip_horizontal true -ssl_seed 1001 -gpu 0

python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder 820_D_CI -n_labels 4000 -translate 2 -flip_horizontal true -c_loss loss_elr_wrap -c_step regular -ssl_seed 1001 -gpu 1

python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder 820_D_CI -n_labels 4000 -translate 2 -flip_horizontal true -c_loss loss_elr_wrap -c_step regular -ssl_seed 1001 -gpu 2

# compare to regular classifier svhn.
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 820_D_VN -n_labels 1000 -translate 2 -c_loss loss_elr_wrap -c_step regular -ssl_seed 1001 -gpu 3

python train_triplegan_final_elr.py ./configs/triple_gan_svhn_noaug_elr.yaml -subfolder 820_D_VN -n_labels 1000 -translate 2 -alpha_c_pdl 0.03 -c_loss loss_elr_wrap -c_step regular -ssl_seed 1001 -gpu 4

python train_triplegan_final_elr.py ./configs/triple_gan_svhn_noaug_elr.yaml -subfolder 820_D_VN -masked_pdl false -consist_pdl true -translate 2 -alpha_c_pdl 0.1 -n_labels 1000 -ssl_seed 1001 -gpu 5

python train_triplegan_final_elr.py ./configs/triple_gan_svhn_noaug_elr.yaml -subfolder 820_D_VN -masked_pdl true -consist_pdl true -translate 2 -alpha_c_pdl 0.1 -n_labels 1000 -ssl_seed 1001 -gpu 6

python train_triplegan_final_elr.py ./configs/triple_gan_svhn_noaug_elr.yaml -subfolder 820_D_VN -masked_pdl false -consist_pdl true -translate 2 -alpha_c_pdl 0.03 -n_labels 1000 -ssl_seed 1001 -gpu 7

python train_triplegan_final_elr.py ./configs/triple_gan_svhn_noaug_elr.yaml -subfolder 820_D_VN -masked_pdl true -consist_pdl true -translate 2 -alpha_c_pdl 0.03 -n_labels 1000 -ssl_seed 1001 -gpu 3




# xuan: g6&g8
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1001 -translate 0 -flip_horizontal false -gpu 0
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1002 -translate 0 -flip_horizontal false -gpu 1
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1003 -translate 0 -flip_horizontal false -gpu 2
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1001 -translate 2 -flip_horizontal true -gpu 3
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1002 -translate 2 -flip_horizontal true -gpu 1
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1003 -translate 2 -flip_horizontal true -gpu 0

python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1002 -translate 2 -alpha_c_pdl 0.1 -flip_horizontal true -gpu 2
python train_triplegan_final_elr.py ./configs/triple_gan_cifar10_noaug_elr.yaml -subfolder RE_CI -ssl_seed 1003 -translate 2 -alpha_c_pdl 0.03 -flip_horizontal true -gpu 3

# baseline svhn 
# xuan g4&11
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 2 -ssl_seed 1001 -gpu 0
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 2 -ssl_seed 1002 -gpu 1
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 2 -ssl_seed 1003 -gpu 2
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 0 -ssl_seed 1001 -gpu 3
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 0 -ssl_seed 1002 -gpu 0
python train_classifier_elr.py ./configs/classifier_svhn_elr.yaml -subfolder 819_D_VN -n_labels 1000 -translate 0 -ssl_seed 1003 -gpu 0

# cifar10 baseline
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal true -ssl_seed 1001 -gpu 0
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal true -ssl_seed 1002 -gpu 1
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal true -ssl_seed 1003 -gpu 0
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal false -ssl_seed 1001 -gpu 1
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal false -ssl_seed 1002 -gpu 2
python train_classifier_elr.py ./configs/classifier_cifar10_elr.yaml -subfolder RE_CI -n_labels 4000 -translate 0 -flip_horizontal false -ssl_seed 1003 -gpu 3

# tiny baseline
# 15000 v.s. 40000

python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 0 -flip_horizontal false -ssl_seed 1001 -gpu 0
python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 0 -flip_horizontal false -ssl_seed 1002 -gpu 1
python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 0 -flip_horizontal false -ssl_seed 1003 -gpu 2
python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 2 -flip_horizontal true -ssl_seed 1001 -gpu 3
python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 2 -flip_horizontal true -ssl_seed 1002 -gpu 2
python train_classifier_elr.py ./configs/classifier_tinyimagenet_elr.yaml -subfolder RE_TI -n_labels 2000 -translate 2 -flip_horizontal true -ssl_seed 1003 -gpu 2