import os
import torch
from torch import nn
from torch.autograd import Variable
import torchvision
import torchvision.datasets as dsets
import torchvision.transforms as transforms
import utils
from arch import define_Gen, define_Dis





def test(args):

    transform = transforms.Compose(
        [transforms.Resize((args.crop_height,args.crop_width)),
         transforms.ToTensor(),
         transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])])

    dataset_dirs = utils.get_testdata_link(args.dataset_dir)

    a_test_data = dsets.ImageFolder(dataset_dirs['testA'], transform=transform)
    b_test_data = dsets.ImageFolder(dataset_dirs['testB'], transform=transform)


    a_test_loader = torch.utils.data.DataLoader(a_test_data, batch_size=args.batch_size, shuffle=True, num_workers=4)
    b_test_loader = torch.utils.data.DataLoader(b_test_data, batch_size=args.batch_size, shuffle=True, num_workers=4)

    Gab = define_Gen(input_nc=3, output_nc=3, ngf=args.ngf, netG='resnet_9blocks', norm=args.norm, 
                                                    use_dropout= not args.no_dropout, gpu_ids=args.gpu_ids)
    Gba = define_Gen(input_nc=3, output_nc=3, ngf=args.ngf, netG='resnet_9blocks', norm=args.norm, 
                                                    use_dropout= not args.no_dropout, gpu_ids=args.gpu_ids)

    utils.print_networks([Gab,Gba], ['Gab','Gba'])

    try:
        # model_save_path = '{}/latest_{}.ckpt'.format(args.checkpoint_dir, os.path.basename(args.dataset_dir))
        # ckpt = utils.load_checkpoint(model_save_path)
        ckpt = utils.load_checkpoint('%s/latest.ckpt' % (args.checkpoint_dir))
        Gab.load_state_dict(ckpt['Gab'])
        Gba.load_state_dict(ckpt['Gba'])
    except:
        print(' [*] No checkpoint!')


    """ run """
    a_real_test = Variable(next(iter(a_test_loader))[0], requires_grad=True)
    b_real_test = Variable(next(iter(b_test_loader))[0], requires_grad=True)
    a_real_test, b_real_test = utils.cuda([a_real_test, b_real_test])
            

    Gab.eval()
    Gba.eval()

    with torch.no_grad():
        a_fake_test = Gab(b_real_test)
        b_fake_test = Gba(a_real_test)
        a_recon_test = Gab(b_fake_test)
        b_recon_test = Gba(a_fake_test)

    pic = (torch.cat([a_real_test, b_fake_test, a_recon_test, b_real_test, a_fake_test, b_recon_test], dim=0).data + 1) / 2.0

    if not os.path.isdir(args.results_dir):
        os.makedirs(args.results_dir)

    dataset_name = os.path.basename(args.dataset_dir)
    test_result_save_path = args.results_dir+'/result_{}.jpg'.format(dataset_name)
    torchvision.utils.save_image(pic, test_result_save_path, nrow=3)

