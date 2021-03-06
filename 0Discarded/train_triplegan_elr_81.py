import copy
import os
import torch
import torch.nn as nn
import torchvision
import numpy as np

from library import inputs
from Utils.checkpoints import save_context, Logger
from Utils import flags
from Utils import config

import Torture
from library import loss_triplegan, evaluation
import library.loss_cla as loss_classifier
from library.mean_teacher import optim_weight_swa


FLAGS = flags.FLAGS
KEY_ARGUMENTS = config.load_config(FLAGS.config_file)
text_logger, MODELS_FOLDER, SUMMARIES_FOLDER = save_context(__file__, KEY_ARGUMENTS)

# FLAGS.g_model_name = FLAGS.model_name
# FLAGS.d_model_name = FLAGS.model_name

torch.manual_seed(1234)
torch.cuda.manual_seed(1235)
np.random.seed(1236)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = True
FLAGS.device = device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
n_iter_d = 5 if "sngan" in FLAGS.g_model_name else 1


def sigmoid_rampup(global_step, start_iter, end_iter):
    if global_step < start_iter:
        return 0.0
    rampup_length = end_iter - start_iter
    cur_ramp = global_step - start_iter
    cur_ramp = np.clip(cur_ramp, 0, rampup_length)
    phase = 1.0 - cur_ramp / rampup_length
    return np.exp(-5.0 * phase * phase)


itr = inputs.get_data_iter(batch_size=FLAGS.bs_c, subset=FLAGS.n_labels)
# itr_u = inputs.get_data_iter(batch_size=FLAGS.bs_c)
netG, optim_G = inputs.get_generator_optimizer()
netD, optim_D = inputs.get_discriminator_optimizer()
netC, optim_c = inputs.get_classifier_optimizer()
netG, netD, netC = netG.to(device), netD.to(device), netC.to(device)
netG = nn.DataParallel(netG)
netD = nn.DataParallel(netD)
netC = nn.DataParallel(netC)
netC_T, _ = inputs.get_classifier_optimizer()
netC_T = netC_T.to(device)
netC_T = nn.DataParallel(netC_T)
netC.train()
netC_T.train()
Torture.update_average(netC_T, netC, 0)
for p in netC_T.parameters():
    p.requires_grad_(False)
if FLAGS.c_step == "ramp_swa":
    netC_swa, _ = inputs.get_classifier_optimizer()
    netC_swa = netC_swa.to(device)
    netC_swa = nn.DataParallel(netC_swa)
    netC_swa.train()
    swa_optim = optim_weight_swa.WeightSWA(netC_swa)
    for p in netC_swa.parameters():
        p.requires_grad_(False)
    Torture.update_average(netC_swa, netC, 0)

checkpoint_io = Torture.utils.checkpoint.CheckpointIO(checkpoint_dir=MODELS_FOLDER)
if FLAGS.c_step == "ramp_swa":
    checkpoint_io.register_modules(
        netG=netG,
        netD=netD,
        netC=netC,
        netC_T=netC_T,
        netC_swa=netC_swa,
        optim_G=optim_G,
        optim_D=optim_D,
        optim_c=optim_c,
    )
else:
    checkpoint_io.register_modules(
        netG=netG,
        netD=netD,
        netC=netC,
        netC_T=netC_T,
        optim_G=optim_G,
        optim_D=optim_D,
        optim_c=optim_c,
    )
logger = Logger(log_dir=SUMMARIES_FOLDER)

realimg, _ = itr.__next__()
print(type(realimg))
torchvision.utils.save_image(
    realimg * 0.5 + 0.5, os.path.join(SUMMARIES_FOLDER, "realimg.png"), 10
)
# train
print_interval = 50
image_interval = 100
max_iter = FLAGS.n_iter
pretrain_inter = FLAGS.n_iter_pretrain
loss_func_g = loss_triplegan.g_loss_dict[FLAGS.gan_type]
loss_func_d = loss_triplegan.d_loss_dict[FLAGS.gan_type]
loss_func_c_adv = loss_triplegan.c_loss_dict[FLAGS.gan_type]
loss_func_c = loss_classifier.c_loss_dict[FLAGS.c_loss]
step_func = loss_classifier.c_step_func[FLAGS.c_step]

logger_prefix = "Itera {}/{} ({:.0f}%)"

for i in range(pretrain_inter):  # 1w
    # tloss, l_loss, u_loss = loss_func_c(netC, netC_T, i, itr, itr_u, device)
    tloss = loss_classifier.loss_elr(netC, i, itr, device)
    # step_func(optim_c, netC, netC_T, i, tloss)
    if FLAGS.c_step == "ramp_swa":
        step_func(optim_c, swa_optim, netC, netC_T, i, tloss)
    else:
        step_func(optim_c, netC, netC_T, i, tloss)

    logger.add("training_pre", "loss", tloss.item(), i + 1)
    # logger.add("training_pre", "l_loss", l_loss.item(), i + 1)
    # logger.add("training_pre", "u_loss", u_loss.item(), i + 1)

    if (i + 1) % print_interval == 0:
        prefix = logger_prefix.format(i + 1, max_iter, (100 * i + 1) / max_iter)
        cats = ["training_pre"]
        logger.log_info(prefix, text_logger.info, cats=cats)


for i in range(pretrain_inter, max_iter + pretrain_inter):
    data, label = itr.__next__()
    data, label = data.to(device), label.to(device)
    # data_u, _ = itr_u.__next__()
    # data_u_d, _ = itr_u.__next__()
    # data_u, data_u_d = data_u.to(device), data_u_d.to(device)

    for _ in range(n_iter_d):
        data, label = itr.__next__()
        data, label = data.to(device), label.to(device)
        data_u, _ = itr.__next__()
        data_u = data_u.to(device)
        sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)

        loss_d, dreal, dfake_g, dfake_c = loss_triplegan.loss_hinge_dis_elr(
            netD, netG, netC, data, sample_z, label, data_u
        )

        optim_D.zero_grad()
        loss_d.backward()
        if FLAGS.clip_value > 0:
            torch.nn.utils.clip_grad_norm_(netD.parameters(), FLAGS.clip_value)
        optim_D.step()

    logger.add("training_d", "loss", loss_d.item(), i + 1)
    logger.add("training_d", "dreal", dreal.item(), i + 1)
    logger.add("training_d", "dfake_g", dfake_g.item(), i + 1)
    logger.add("training_d", "dfake_c", dfake_c.item(), i + 1)

    sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)
    loss_g, fake_g = loss_func_g(netD, netG, sample_z, label)
    optim_G.zero_grad()
    loss_g.backward()
    if FLAGS.clip_value > 0:
        torch.nn.utils.clip_grad_norm_(netG.parameters(), FLAGS.clip_value)
    optim_G.step()

    logger.add("training_g", "loss", loss_g.item(), i + 1)
    logger.add("training_g", "fake_g", fake_g.item(), i + 1)

    data, _ = itr.__next__()
    data = data.to(device)
    tloss_c_adv, fake_c = loss_func_c_adv(netD, netC, data)
    adv_ramp_coe = sigmoid_rampup(i, FLAGS.adv_ramp_start, FLAGS.adv_ramp_end)
    loss_c_adv = tloss_c_adv * adv_ramp_coe

    loss_c_ssl = loss_classifier.loss_elr(netC, i, itr, device)

    sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)
    tloss_c_pdl = loss_triplegan.pseudo_discriminative_loss(netC, netG, sample_z, label)
    pdl_ramp_coe = sigmoid_rampup(i, FLAGS.pdl_ramp_start, FLAGS.pdl_ramp_end)
    loss_c_pdl = tloss_c_pdl * pdl_ramp_coe

    loss_c = (
        FLAGS.alpha_c_adv * loss_c_adv + FLAGS.alpha_c_pdl * loss_c_pdl + loss_c_ssl
    )

    step_func(optim_c, netC, netC_T, i, loss_c)

    logger.add("training_c", "loss", loss_c.item(), i + 1)
    logger.add("training_c", "loss_adv", loss_c_adv.item(), i + 1)
    logger.add("training_c", "loss_ssl", loss_c_ssl.item(), i + 1)
    logger.add("training_c", "loss_pdl", loss_c_pdl.item(), i + 1)
    logger.add("training_c", "fake_c", fake_c.item(), i + 1)

    if (i + 1) % print_interval == 0:
        prefix = logger_prefix.format(i + 1, max_iter, (100 * i + 1) / max_iter)
        cats = ["training_d", "training_g", "training_c"]
        logger.log_info(prefix, text_logger.info, cats=cats)

    if (i + 1) % image_interval == 0:
        netC.eval()
        netC_T.eval()
        with torch.no_grad():
            sample_z = torch.randn((FLAGS.bs_g // 10) * 10, FLAGS.g_z_dim).to(device)
            tlabel = label[: FLAGS.bs_g // 10]
            tlabel = torch.cat([tlabel for _ in range(10)], 0)
            x_fake = netG(sample_z, tlabel)
            logger.add_imgs(x_fake, "img{:08d}".format(i + 1), nrow=FLAGS.bs_g // 10)
            total_t, correct_t, loss_t = evaluation.test_classifier(netC)
            total_tt, correct_tt, loss_tt = evaluation.test_classifier(netC_T)
        netC.train()
        netC_T.train()

        logger.add("testing", "loss", loss_t.item(), i + 1)
        logger.add("testing", "accuracy", 100 * (correct_t / total_t), i + 1)
        logger.add("testing", "loss_t", loss_tt.item(), i + 1)
        logger.add("testing", "accuracy_t", 100 * (correct_tt / total_tt), i + 1)
        str_meg = logger_prefix.format(i + 1, max_iter, 100 * ((i + 1) / max_iter))
        logger.log_info(str_meg, text_logger.info, ["testing"])

    if (i + 1) % FLAGS.save_every == 0:
        logger.save_stats("Model_stats.pkl")
        file_name = "model" + str(i + 1) + ".pt"
        checkpoint_io.save(file_name)
