import copy

import torch
import torch.nn as nn
import numpy as np

from library import inputs
from Utils.checkpoints import save_context, Logger
from Utils import flags
from Utils import config

import Torture
from library import loss_triplegan, loss_classifier, evaluation

FLAGS = flags.FLAGS
KEY_ARGUMENTS = config.load_config(FLAGS.config_file)
text_logger, MODELS_FOLDER, SUMMARIES_FOLDER = save_context(__file__, KEY_ARGUMENTS)

torch.manual_seed(1234)
torch.cuda.manual_seed(1235)
np.random.seed(1236)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = True
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


itr = inputs.get_data_iter(batch_size=FLAGS.bs_c, subset=1000)
itr_u = inputs.get_data_iter(batch_size=FLAGS.bs_c)
# itr_t = inputs.get_data_iter_twice(subset=1000)
# itr_ut = inputs.get_data_iter_twice()
netG, optim_G = inputs.get_generator_optimizer()
netD, optim_D = inputs.get_discriminator_optimizer()
netC, optim_c = inputs.get_classifier_optimizer()

netG, netD, netC = netG.to(device), netD.to(device), netC.to(device)
netG = nn.DataParallel(netG)
netD = nn.DataParallel(netD)
netC = nn.DataParallel(netC)

checkpoint_io = Torture.utils.checkpoint.CheckpointIO(checkpoint_dir=MODELS_FOLDER)
checkpoint_io.register_modules(
    netG=netG, netD=netD, netC=netC, optim_G=optim_G, optim_D=optim_D, optim_c=optim_c
)
logger = Logger(log_dir=SUMMARIES_FOLDER)

# train
print_interval = 50
image_interval = 500
max_iter = FLAGS.n_iter
loss_func_g = loss_triplegan.g_loss_dict[FLAGS.gan_type]
loss_func_d = loss_triplegan.d_loss_dict[FLAGS.gan_type]
loss_func_c_adv = loss_triplegan.c_loss_dict[FLAGS.gan_type]
loss_func_c_ssl = loss_classifier.c_loss_dict[FLAGS.c_loss]

logger_prefix = "Itera {}/{} ({:.0f}%)"
for i in range(max_iter):
    data, label = itr.__next__()
    data, label = data.to(device), label.to(device)
    data_u, _ = itr_u.__next__()
    data_u_d, _ = itr_u.__next__()
    data_u, data_u_d = data_u.to(device), data_u_d.to(device)

    sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)
    loss_d, dreal, dfake_g, dfake_c = loss_func_d(
        netD, netG, netC, data, sample_z, label, data_u, data_u_d
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

    loss_c_adv, fake_c = loss_func_c_adv(netD, netC, data_u)
    loss_c_ssl = loss_func_c_ssl(netC, data, label, data_u)
    if i > FLAGS.psl_iters:
        sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)
        loss_c_pdl = loss_triplegan.pseudo_discriminative_loss(
            netC, netG, sample_z, label
        )
    else:
        loss_c_pdl = torch.zeros_like(loss_c_ssl)
    loss_c = (
        FLAGS.alpha_c_adv * loss_c_adv + FLAGS.alpha_c_pdl * loss_c_pdl + loss_c_ssl
    )
    optim_c.zero_grad()
    loss_c.backward()
    if FLAGS.clip_value > 0:
        torch.nn.utils.clip_grad_norm_(netC.parameters(), FLAGS.clip_value)
    optim_c.step()
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
        with torch.no_grad():
            sample_z = torch.randn(FLAGS.bs_g, FLAGS.g_z_dim).to(device)
            tlabel = label[: FLAGS.bs_g // 10]
            tlabel = torch.cat([tlabel for _ in range(10)], 0)
            x_fake = netG(sample_z, tlabel)
            logger.add_imgs(x_fake, "img{:08d}".format(i + 1), nrow=FLAGS.bs_g // 10)
            total_t, correct_t, loss_t = evaluation.test_classifier(netC)

        logger.add("testing", "loss", loss_t.item(), i + 1)
        logger.add("testing", "total_test", total_t, i + 1)
        logger.add("testing", "correct_test", correct_t, i + 1)
        logger.add("testing", "accuracy", 100 * (correct_t / total_t), i + 1)
        str_meg = logger_prefix.format(i + 1, max_iter, 100 * ((i + 1) / max_iter))
        logger.log_info(str_meg, text_logger.info, ["testing"])

    if (i + 1) % FLAGS.save_every == 0:
        logger.save_stats("Model_stats.pkl")
        file_name = "model" + str(i + 1) + ".pt"
        checkpoint_io.save(file_name)
